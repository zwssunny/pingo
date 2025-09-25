# -*- coding: utf-8 -*-
"""
错误处理工具模块
提供装饰器、上下文管理器和重试机制
"""

import time
import functools
import threading
from typing import Type, Union, List, Callable, Optional, Any, Dict
from contextlib import contextmanager

from common.log import logger
from common.exceptions import (
    PingoBaseException, SystemException, ASRException, TTSException,
    NLUException, AIException, NetworkException, TimeoutException,
    ErrorCode
)


class ErrorHandler:
    """错误处理器"""
    
    @staticmethod
    def log_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """统一错误日志记录"""
        context = context or {}
        
        if isinstance(error, PingoBaseException):
            error_dict = error.to_dict()
            logger.error(
                f"[{error_dict['error_name']}] {error_dict['message']}", 
                extra={
                    "error_code": error_dict["error_code"],
                    "details": error_dict["details"],
                    "context": context
                },
                exc_info=error.original_exception
            )
        else:
            logger.error(
                f"未处理异常: {str(error)}", 
                extra={"context": context},
                exc_info=True
            )
    
    @staticmethod
    def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None, 
                    fallback_result: Any = None) -> Any:
        """统一错误处理"""
        ErrorHandler.log_error(error, context)
        
        # 根据错误类型执行不同的处理策略
        if isinstance(error, TimeoutException):
            # 超时错误，可能需要重试
            pass
        elif isinstance(error, NetworkException):
            # 网络错误，可能需要切换服务
            pass
        elif isinstance(error, ASRException):
            # ASR错误，可能需要降级处理
            pass
        
        return fallback_result


def error_handler(
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    fallback_result: Any = None,
    log_context: Optional[Dict[str, Any]] = None,
    reraise: bool = False
):
    """
    错误处理装饰器
    
    Args:
        exceptions: 要捕获的异常类型
        fallback_result: 发生错误时的默认返回值
        log_context: 日志上下文信息
        reraise: 是否重新抛出异常
    """
    if not isinstance(exceptions, (list, tuple)):
        exceptions = [exceptions]
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except tuple(exceptions) as e:
                context = log_context or {}
                context.update({
                    "function": func.__name__,
                    "module": func.__module__,
                    "args": str(args)[:200],  # 限制参数长度
                    "kwargs": str(kwargs)[:200]
                })
                
                result = ErrorHandler.handle_error(e, context, fallback_result)
                
                if reraise:
                    raise
                return result
        return wrapper
    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    on_retry: Optional[Callable] = None
):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟倍数
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数
    """
    if not isinstance(exceptions, (list, tuple)):
        exceptions = [exceptions]
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # 最后一次尝试失败，记录错误并抛出
                        ErrorHandler.log_error(e, {
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_retries": max_retries
                        })
                        raise
                    
                    # 记录重试信息
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败，{current_delay}秒后重试: {str(e)}"
                    )
                    
                    if on_retry:
                        on_retry(attempt + 1, e)
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        return wrapper
    return decorator


@contextmanager
def error_context(
    operation: str,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    fallback_result: Any = None,
    reraise: bool = True
):
    """
    错误处理上下文管理器
    
    Args:
        operation: 操作描述
        exceptions: 要捕获的异常类型
        fallback_result: 发生错误时的默认返回值
        reraise: 是否重新抛出异常
    """
    if not isinstance(exceptions, (list, tuple)):
        exceptions = [exceptions]
    
    try:
        yield
    except tuple(exceptions) as e:
        context = {
            "operation": operation,
            "thread_id": threading.current_thread().ident
        }
        
        ErrorHandler.handle_error(e, context, fallback_result)
        
        if reraise:
            raise


class CircuitBreaker:
    """熔断器模式实现"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """通过熔断器调用函数"""
        with self._lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time >= self.timeout:
                    self.state = "HALF_OPEN"
                    logger.info("熔断器状态变更为 HALF_OPEN")
                else:
                    raise SystemException("服务熔断中，请稍后重试")
            
            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info("熔断器状态变更为 CLOSED")
                return result
            
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(f"熔断器状态变更为 OPEN，失败次数: {self.failure_count}")
                
                raise


def safe_execute(
    func: Callable,
    *args,
    default_result: Any = None,
    max_retries: int = 1,
    timeout: Optional[float] = None,
    **kwargs
) -> Any:
    """
    安全执行函数，包含错误处理和超时控制
    
    Args:
        func: 要执行的函数
        default_result: 默认返回值
        max_retries: 最大重试次数
        timeout: 超时时间（秒）
        *args, **kwargs: 函数参数
    """
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutException(f"函数 {func.__name__} 执行超时")
    
    for attempt in range(max_retries + 1):
        try:
            if timeout:
                # 设置超时处理（仅在Unix系统上有效）
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(timeout))
            
            result = func(*args, **kwargs)
            
            if timeout:
                signal.alarm(0)  # 取消超时
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
            
        except Exception as e:
            if timeout:
                signal.alarm(0)  # 取消超时
                signal.signal(signal.SIGALRM, old_handler)
            
            if attempt == max_retries:
                ErrorHandler.log_error(e, {
                    "function": func.__name__,
                    "attempt": attempt + 1,
                    "max_retries": max_retries
                })
                return default_result
            
            logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次执行失败，准备重试: {str(e)}")
            time.sleep(0.5 * (attempt + 1))  # 递增延迟
    
    return default_result


# 创建全局熔断器实例
asr_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)
tts_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)
ai_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)