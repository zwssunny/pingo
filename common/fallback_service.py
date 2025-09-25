# -*- coding: utf-8 -*-
"""
服务降级和错误恢复机制
当主要服务不可用时，提供备用服务和恢复策略
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

from common.log import logger
from common.exceptions import (
    PingoBaseException, ASRException, TTSException, 
    AIException, NetworkException, SystemException
)


class ServiceStatus(Enum):
    """服务状态枚举"""
    AVAILABLE = "available"        # 可用
    DEGRADED = "degraded"         # 降级
    UNAVAILABLE = "unavailable"   # 不可用
    RECOVERING = "recovering"     # 恢复中


class FallbackService:
    """降级服务管理器"""
    
    def __init__(self):
        self.services = {}
        self.service_status = {}
        self.failure_counts = {}
        self.last_check_times = {}
        self.recovery_attempts = {}
        self._lock = threading.Lock()
    
    def register_service(
        self, 
        service_name: str, 
        primary_service: Callable,
        fallback_services: List[Callable] = None,
        health_check: Callable = None,
        max_failures: int = 3,
        recovery_interval: int = 300  # 5分钟
    ):
        """
        注册服务及其降级方案
        
        Args:
            service_name: 服务名称
            primary_service: 主要服务
            fallback_services: 备用服务列表
            health_check: 健康检查函数
            max_failures: 最大失败次数
            recovery_interval: 恢复检查间隔（秒）
        """
        with self._lock:
            self.services[service_name] = {
                "primary": primary_service,
                "fallbacks": fallback_services or [],
                "health_check": health_check,
                "max_failures": max_failures,
                "recovery_interval": recovery_interval
            }
            
            self.service_status[service_name] = ServiceStatus.AVAILABLE
            self.failure_counts[service_name] = 0
            self.last_check_times[service_name] = 0
            self.recovery_attempts[service_name] = 0
    
    def call_service(self, service_name: str, *args, **kwargs) -> Any:
        """
        调用服务，自动处理降级
        
        Args:
            service_name: 服务名称
            *args, **kwargs: 服务参数
            
        Returns:
            服务调用结果
        """
        if service_name not in self.services:
            raise SystemException(f"未注册的服务: {service_name}")
        
        service_config = self.services[service_name]
        
        # 检查是否需要恢复服务
        self._check_service_recovery(service_name)
        
        # 尝试主要服务
        if self.service_status[service_name] in [ServiceStatus.AVAILABLE, ServiceStatus.RECOVERING]:
            try:
                result = service_config["primary"](*args, **kwargs)
                # 服务调用成功，重置失败计数
                with self._lock:
                    self.failure_counts[service_name] = 0
                    self.service_status[service_name] = ServiceStatus.AVAILABLE
                    self.recovery_attempts[service_name] = 0
                
                logger.debug(f"服务 {service_name} 主要服务调用成功")
                return result
                
            except Exception as e:
                self._handle_service_failure(service_name, e)
        
        # 主要服务不可用，尝试备用服务
        return self._call_fallback_services(service_name, *args, **kwargs)
    
    def _handle_service_failure(self, service_name: str, error: Exception):
        """处理服务失败"""
        with self._lock:
            self.failure_counts[service_name] += 1
            
            if self.failure_counts[service_name] >= self.services[service_name]["max_failures"]:
                self.service_status[service_name] = ServiceStatus.UNAVAILABLE
                logger.warning(f"服务 {service_name} 标记为不可用，失败次数: {self.failure_counts[service_name]}")
            else:
                self.service_status[service_name] = ServiceStatus.DEGRADED
                logger.warning(f"服务 {service_name} 调用失败 ({self.failure_counts[service_name]}/{self.services[service_name]['max_failures']}): {error}")
    
    def _call_fallback_services(self, service_name: str, *args, **kwargs) -> Any:
        """调用备用服务"""
        service_config = self.services[service_name]
        fallback_services = service_config["fallbacks"]
        
        if not fallback_services:
            raise SystemException(f"服务 {service_name} 不可用且无备用服务")
        
        for i, fallback_service in enumerate(fallback_services):
            try:
                logger.info(f"尝试使用备用服务 {service_name}[{i}]")
                result = fallback_service(*args, **kwargs)
                
                with self._lock:
                    self.service_status[service_name] = ServiceStatus.DEGRADED
                
                logger.info(f"备用服务 {service_name}[{i}] 调用成功")
                return result
                
            except Exception as e:
                logger.warning(f"备用服务 {service_name}[{i}] 调用失败: {e}")
                continue
        
        # 所有服务都不可用
        raise SystemException(f"服务 {service_name} 及所有备用服务都不可用")
    
    def _check_service_recovery(self, service_name: str):
        """检查服务是否可以恢复"""
        if self.service_status[service_name] != ServiceStatus.UNAVAILABLE:
            return
        
        current_time = time.time()
        service_config = self.services[service_name]
        
        # 检查是否到了恢复检查时间
        if current_time - self.last_check_times[service_name] < service_config["recovery_interval"]:
            return
        
        with self._lock:
            self.last_check_times[service_name] = current_time
            self.service_status[service_name] = ServiceStatus.RECOVERING
            self.recovery_attempts[service_name] += 1
        
        logger.info(f"尝试恢复服务 {service_name} (第 {self.recovery_attempts[service_name]} 次)")
        
        # 如果有健康检查函数，使用它来检查服务状态
        health_check = service_config.get("health_check")
        if health_check:
            try:
                if health_check():
                    with self._lock:
                        self.service_status[service_name] = ServiceStatus.AVAILABLE
                        self.failure_counts[service_name] = 0
                        self.recovery_attempts[service_name] = 0
                    logger.info(f"服务 {service_name} 恢复成功")
                else:
                    with self._lock:
                        self.service_status[service_name] = ServiceStatus.UNAVAILABLE
                    logger.warning(f"服务 {service_name} 健康检查失败")
            except Exception as e:
                with self._lock:
                    self.service_status[service_name] = ServiceStatus.UNAVAILABLE
                logger.warning(f"服务 {service_name} 健康检查异常: {e}")
    
    def get_service_status(self, service_name: str) -> ServiceStatus:
        """获取服务状态"""
        return self.service_status.get(service_name, ServiceStatus.UNAVAILABLE)
    
    def get_all_service_status(self) -> Dict[str, ServiceStatus]:
        """获取所有服务状态"""
        return self.service_status.copy()
    
    def force_recover_service(self, service_name: str):
        """强制恢复服务"""
        if service_name in self.services:
            with self._lock:
                self.service_status[service_name] = ServiceStatus.AVAILABLE
                self.failure_counts[service_name] = 0
                self.recovery_attempts[service_name] = 0
                self.last_check_times[service_name] = 0
            logger.info(f"强制恢复服务 {service_name}")


# 创建全局降级服务管理器
fallback_manager = FallbackService()


def simple_tts_fallback(text: str) -> str:
    """简单的TTS降级服务 - 返回文本而不是语音"""
    logger.info(f"TTS降级服务: {text}")
    return text


def simple_asr_fallback(audio_file: str) -> str:
    """简单的ASR降级服务 - 返回固定文本"""
    logger.warning("ASR服务不可用，使用降级服务")
    return "抱歉，语音识别服务暂时不可用"


def simple_ai_fallback(query: str, *args, **kwargs) -> str:
    """简单的AI降级服务 - 返回固定回复"""
    fallback_responses = [
        "抱歉，我现在无法理解您的话。",
        "系统正在维护中，请稍后再试。",
        "我遇到了一些技术问题，请您重新说一遍。"
    ]
    
    # 根据查询内容选择合适的回复
    if "你好" in query or "hello" in query.lower():
        return "您好！很高兴见到您。"
    elif "谢谢" in query or "thank" in query.lower():
        return "不客气！"
    else:
        import random
        return random.choice(fallback_responses)


def register_default_fallback_services():
    """注册默认的降级服务"""
    # 注册TTS降级服务
    fallback_manager.register_service(
        "tts",
        primary_service=None,  # 将在运行时设置
        fallback_services=[simple_tts_fallback],
        max_failures=3,
        recovery_interval=180
    )
    
    # 注册ASR降级服务
    fallback_manager.register_service(
        "asr",
        primary_service=None,  # 将在运行时设置
        fallback_services=[simple_asr_fallback],
        max_failures=2,
        recovery_interval=120
    )
    
    # 注册AI降级服务
    fallback_manager.register_service(
        "ai",
        primary_service=None,  # 将在运行时设置
        fallback_services=[simple_ai_fallback],
        max_failures=5,
        recovery_interval=300
    )
    
    logger.info("默认降级服务注册完成")


# 自动注册默认服务
register_default_fallback_services()