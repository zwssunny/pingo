# Pingo错误处理系统优化指南

## 概述

本指南介绍了Pingo项目中全新的错误处理系统，包括统一异常类、错误处理装饰器、服务降级机制和错误恢复策略。

## 🎯 优化目标

1. **统一错误处理**: 提供一致的错误处理方式
2. **提高系统稳定性**: 减少因单点故障导致的系统崩溃
3. **增强可观测性**: 更详细的错误日志和监控
4. **自动恢复**: 智能的错误恢复和服务降级
5. **开发友好**: 简化错误处理代码编写

## 🏗️ 架构组件

### 1. 自定义异常类 (`common/exceptions.py`)

```python
# 错误代码枚举
class ErrorCode(Enum):
    ASR_ENGINE_ERROR = 2000
    TTS_SYNTHESIS_ERROR = 3001
    AI_CHAT_ERROR = 5001
    # ... 更多错误代码

# 基础异常类
class PingoBaseException(Exception):
    def __init__(self, message, error_code, details=None, original_exception=None):
        # 包含错误代码、详细信息和原始异常
        pass

# 专门异常类
class ASRException(PingoBaseException): pass
class TTSException(PingoBaseException): pass
class AIException(PingoBaseException): pass
```

### 2. 错误处理装饰器 (`common/error_handler.py`)

```python
# 基础错误处理装饰器
@error_handler(
    exceptions=[ASRException, Exception],
    fallback_result="默认值",
    log_context={"component": "asr"}
)
def your_function():
    pass

# 重试装饰器
@retry_on_error(
    max_retries=3,
    delay=1.0,
    exceptions=[NetworkException]
)
def network_request():
    pass

# 熔断器模式
circuit_breaker.call(risky_function, *args)
```

### 3. 服务降级机制 (`common/fallback_service.py`)

```python
# 注册服务降级
fallback_manager.register_service(
    "tts",
    primary_service=main_tts_service,
    fallback_services=[backup_tts, simple_tts],
    max_failures=3
)

# 调用服务（自动降级）
result = fallback_manager.call_service("tts", text)
```

## 🔧 使用方法

### 在现有代码中应用

#### 1. conversation.py 优化示例

**优化前:**
```python
def doConverse(self, fp, callback=None, onSay=None, onStream=None):
    try:
        query = self.asr.transcribe(fp)
    except Exception as e:
        logger.critical(f"ASR识别失败：{e}", stack_info=True)
    try:
        self.doResponse(query, callback, onSay, onStream)
    except Exception as e:
        logger.critical(f"回复失败：{e}", stack_info=True)
```

**优化后:**
```python
@error_handler(
    exceptions=[ASRException, Exception],
    log_context={"operation": "conversation_converse"}
)
def doConverse(self, fp, callback=None, onSay=None, onStream=None):
    # ASR识别阶段
    try:
        query = asr_circuit_breaker.call(self.asr.transcribe, fp)
        if not query or not query.strip():
            self.pardon()
            return
    except Exception as e:
        raise ASRTranscribeException(
            f"语音识别失败: {str(e)}",
            details={"audio_file": fp},
            original_exception=e
        )
    
    # 响应处理阶段
    try:
        self.doResponse(query, callback, onSay, onStream)
    except Exception as e:
        self.say("抱歉，我遇到了一些问题，请稍后再试。")
        raise AIException(
            f"对话响应失败: {str(e)}",
            details={"query": query},
            original_exception=e
        )
```

#### 2. AI.py 优化示例

**优化前:**
```python
def chat(self, texts, parsed):
    try:
        result = self.unit.getSay(parsed)
        return result
    except Exception:
        logger.error("聊天机器人错误")
        return ""
```

**优化后:**
```python
@error_handler(
    exceptions=[AIException, Exception],
    fallback_result="抱歉，我现在无法理解您的话。",
    log_context={"operation": "unit_robot_chat"}
)
def chat(self, texts, parsed):
    try:
        result = safe_execute(
            self.unit.getSay,
            parsed,
            default_result=None,
            max_retries=2
        )
        
        if not result:
            raise AIChatException("百度UNIT服务返回空结果")
        
        return result
        
    except Exception as e:
        raise AIChatException(
            f"百度UNIT机器人聊天失败: {str(e)}",
            details={"parsed_result": str(parsed)[:200]},
            original_exception=e
        )
```

### 新功能集成

#### 1. 在conversation.py中集成服务降级

```python
# 在__init__方法中注册服务
def __init__(self):
    # ... 原有代码
    
    # 注册ASR服务降级
    fallback_manager.register_service(
        "asr_service",
        primary_service=self.asr.transcribe,
        fallback_services=[self._fallback_asr],
        health_check=self._check_asr_health,
        max_failures=3
    )

def _fallback_asr(self, audio_file):
    """ASR降级服务"""
    return "抱歉，语音识别服务暂时不可用，请使用文字输入。"

def _check_asr_health(self):
    """ASR健康检查"""
    try:
        # 简单的健康检查
        return self.asr is not None
    except:
        return False
```

#### 2. 在TTS中使用熔断器

```python
from common.error_handler import tts_circuit_breaker

def say(self, msg, plugin="", append_history=True):
    try:
        voice = tts_circuit_breaker.call(
            self.tts.get_speech, msg
        )
        # ... 后续处理
    except SystemException:
        # 熔断器开启，使用文本输出
        logger.info(f"TTS服务熔断，文本输出: {msg}")
```

## 📊 监控和日志

### 1. 错误统计

```python
# 获取服务状态
status = fallback_manager.get_all_service_status()
print(f"服务状态: {status}")

# 熔断器状态
print(f"ASR熔断器状态: {asr_circuit_breaker.state}")
```

### 2. 结构化日志

错误日志现在包含：
- 错误代码和类型
- 详细的上下文信息
- 原始异常堆栈
- 操作描述

```python
# 日志示例
{
  "level": "ERROR",
  "message": "[ASR_TRANSCRIBE_ERROR] 语音识别失败: 音频文件损坏",
  "error_code": 2001,
  "details": {"audio_file": "test.wav"},
  "context": {"operation": "conversation_converse"},
  "timestamp": "2023-01-01T12:00:00"
}
```

## 🚀 迁移指南

### 1. 替换现有异常处理

1. **导入新模块**:
```python
from common.exceptions import ASRException, TTSException, AIException
from common.error_handler import error_handler, retry_on_error
```

2. **替换try-catch块**:
```python
# 旧方式
try:
    result = risky_function()
except Exception as e:
    logger.error(f"操作失败: {e}")
    return default_value

# 新方式
@error_handler(exceptions=[SpecificException], fallback_result=default_value)
def safe_risky_function():
    return risky_function()
```

3. **使用具体异常类型**:
```python
# 旧方式
raise Exception("ASR识别失败")

# 新方式
raise ASRTranscribeException(
    "语音识别失败",
    details={"audio_file": file_path},
    original_exception=e
)
```

### 2. 配置服务降级

```python
# 在系统初始化时配置
def setup_fallback_services():
    # ASR服务
    fallback_manager.register_service(
        "asr",
        primary_service=primary_asr.transcribe,
        fallback_services=[backup_asr.transcribe, offline_asr.transcribe]
    )
    
    # TTS服务
    fallback_manager.register_service(
        "tts",
        primary_service=primary_tts.synthesize,
        fallback_services=[backup_tts.synthesize, text_output]
    )
```

## 📋 最佳实践

### 1. 异常处理原则

- **具体化**: 使用具体的异常类型而不是通用Exception
- **上下文**: 提供足够的错误上下文信息
- **分层**: 在不同层次处理不同类型的错误
- **用户友好**: 向用户提供有意义的错误反馈

### 2. 服务设计原则

- **单一职责**: 每个服务专注于单一功能
- **故障隔离**: 服务间故障互不影响
- **渐进降级**: 提供多级降级方案
- **快速恢复**: 实现自动故障恢复

### 3. 监控和告警

- **关键指标**: 监控错误率、响应时间、服务可用性
- **阈值告警**: 设置合理的告警阈值
- **趋势分析**: 分析错误趋势和模式

## 🔍 故障排查

### 1. 常见问题

**问题**: 服务一直处于降级状态
**解决**: 检查健康检查函数和恢复间隔设置

**问题**: 熔断器频繁开启
**解决**: 调整失败阈值或优化服务稳定性

**问题**: 错误日志过多
**解决**: 检查日志级别设置和异常处理逻辑

### 2. 调试工具

```python
# 查看服务状态
print(fallback_manager.get_all_service_status())

# 强制恢复服务
fallback_manager.force_recover_service("asr")

# 查看熔断器状态
print(f"熔断器状态: {circuit_breaker.state}")
```

## 🎉 总结

新的错误处理系统提供了：

1. **🛡️ 更强的稳定性**: 通过熔断器和降级机制防止级联故障
2. **🔍 更好的可观测性**: 结构化日志和详细的错误信息
3. **🚀 更快的恢复**: 自动故障检测和恢复机制
4. **👥 更好的用户体验**: 优雅的错误处理和友好的反馈
5. **🔧 更易的维护**: 统一的错误处理模式和最佳实践

通过逐步采用这套错误处理系统，Pingo项目将具备更好的生产环境稳定性和可维护性。