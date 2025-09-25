# -*- coding: utf-8 -*-
"""
错误处理系统使用示例
展示如何在Pingo项目中使用新的错误处理机制
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.exceptions import *
from common.error_handler import *
from common.fallback_service import fallback_manager
from common.log import logger


# 示例1: 使用错误处理装饰器
@error_handler(
    exceptions=[ASRException, NetworkException],
    fallback_result="识别失败",
    log_context={"component": "asr_service"}
)
def example_asr_transcribe(audio_file: str) -> str:
    """模拟ASR转录服务"""
    if "error" in audio_file:
        raise ASRTranscribeException("音频文件损坏", details={"file": audio_file})
    return f"转录结果: {audio_file}"


# 示例2: 使用重试装饰器
@retry_on_error(
    max_retries=3,
    delay=1.0,
    exceptions=[NetworkException],
    on_retry=lambda attempt, error: logger.info(f"第{attempt}次重试，错误: {error}")
)
def example_network_request(url: str) -> str:
    """模拟网络请求"""
    import random
    if random.random() < 0.7:  # 70%的失败率
        raise NetworkException("网络连接失败", details={"url": url})
    return f"请求成功: {url}"


# 示例3: 使用错误上下文管理器
def example_tts_synthesis(text: str) -> str:
    """模拟TTS合成"""
    with error_context("TTS语音合成", exceptions=[TTSException]):
        if len(text) > 100:
            raise TTSSynthesisException("文本过长", details={"length": len(text)})
        return f"合成音频: {text}"


# 示例4: 使用熔断器
def example_ai_chat_with_circuit_breaker(query: str) -> str:
    """使用熔断器的AI聊天"""
    def ai_service(q):
        import random
        if random.random() < 0.8:  # 80%的失败率
            raise AIChatException("AI服务暂时不可用")
        return f"AI回复: {q}"
    
    try:
        return ai_circuit_breaker.call(ai_service, query)
    except SystemException as e:
        return "AI服务正在维护中，请稍后再试。"


# 示例5: 使用服务降级
def example_fallback_service():
    """服务降级示例"""
    
    def primary_tts(text):
        """主要TTS服务"""
        if "error" in text:
            raise TTSException("TTS合成失败")
        return f"高质量语音: {text}"
    
    def fallback_tts(text):
        """备用TTS服务"""
        return f"普通质量语音: {text}"
    
    def simple_tts(text):
        """简单TTS服务"""
        return f"文本输出: {text}"
    
    # 注册服务
    fallback_manager.register_service(
        "example_tts",
        primary_service=primary_tts,
        fallback_services=[fallback_tts, simple_tts],
        max_failures=2
    )
    
    # 测试服务调用
    test_texts = ["正常文本", "error文本", "另一个正常文本"]
    
    for text in test_texts:
        try:
            result = fallback_manager.call_service("example_tts", text)
            print(f"TTS结果: {result}")
        except Exception as e:
            print(f"TTS失败: {e}")


# 示例6: 使用安全执行函数
def example_safe_execute():
    """安全执行示例"""
    
    def unreliable_function(data):
        import random
        if random.random() < 0.5:
            raise Exception("随机失败")
        return f"处理结果: {data}"
    
    # 安全执行，带重试和默认值
    result = safe_execute(
        unreliable_function,
        "测试数据",
        default_result="默认结果",
        max_retries=3
    )
    
    print(f"安全执行结果: {result}")


# 示例7: 自定义异常处理
class CustomService:
    """自定义服务类，展示异常处理最佳实践"""
    
    @error_handler(
        exceptions=[Exception],
        log_context={"service": "custom_service"}
    )
    def process_data(self, data: dict) -> dict:
        """处理数据"""
        try:
            # 验证输入
            if not isinstance(data, dict):
                raise SystemException(
                    "输入数据格式错误",
                    details={"expected": "dict", "actual": type(data).__name__}
                )
            
            if "required_field" not in data:
                raise SystemException(
                    "缺少必需字段",
                    details={"missing_field": "required_field", "data": data}
                )
            
            # 模拟处理
            result = {
                "status": "success",
                "processed_data": data,
                "timestamp": "2023-01-01"
            }
            
            return result
            
        except SystemException:
            # 重新抛出系统异常
            raise
        except Exception as e:
            # 包装其他异常
            raise SystemException(
                f"数据处理失败: {str(e)}",
                details={"input_data": data},
                original_exception=e
            )


def main():
    """主函数，运行所有示例"""
    print("=== Pingo错误处理系统使用示例 ===\n")
    
    # 示例1: 错误处理装饰器
    print("1. 错误处理装饰器示例:")
    try:
        result1 = example_asr_transcribe("normal_audio.wav")
        print(f"   成功: {result1}")
        
        result2 = example_asr_transcribe("error_audio.wav")
        print(f"   降级: {result2}")
    except Exception as e:
        print(f"   异常: {e}")
    
    print()
    
    # 示例2: 重试装饰器
    print("2. 重试装饰器示例:")
    try:
        result = example_network_request("http://api.example.com")
        print(f"   成功: {result}")
    except Exception as e:
        print(f"   最终失败: {e}")
    
    print()
    
    # 示例3: 错误上下文管理器
    print("3. 错误上下文管理器示例:")
    try:
        result = example_tts_synthesis("短文本")
        print(f"   成功: {result}")
    except Exception as e:
        print(f"   失败: {e}")
    
    print()
    
    # 示例4: 熔断器
    print("4. 熔断器示例:")
    for i in range(8):
        result = example_ai_chat_with_circuit_breaker(f"查询{i}")
        print(f"   查询{i}: {result}")
    
    print()
    
    # 示例5: 服务降级
    print("5. 服务降级示例:")
    example_fallback_service()
    
    print()
    
    # 示例6: 安全执行
    print("6. 安全执行示例:")
    example_safe_execute()
    
    print()
    
    # 示例7: 自定义异常处理
    print("7. 自定义异常处理示例:")
    service = CustomService()
    
    # 正常情况
    try:
        result = service.process_data({"required_field": "value"})
        print(f"   成功: {result}")
    except Exception as e:
        print(f"   失败: {e}")
    
    # 错误情况
    try:
        result = service.process_data({"wrong_field": "value"})
        print(f"   成功: {result}")
    except Exception as e:
        print(f"   失败: {e}")


if __name__ == "__main__":
    main()