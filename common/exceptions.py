# -*- coding: utf-8 -*-
"""
统一异常处理模块
定义了Pingo系统中的所有自定义异常类
"""

import traceback
from enum import Enum
from typing import Optional, Dict, Any


class ErrorCode(Enum):
    """错误代码枚举"""
    # 系统级错误 1000-1999
    SYSTEM_ERROR = 1000
    CONFIG_ERROR = 1001
    INITIALIZATION_ERROR = 1002
    RESOURCE_ERROR = 1003
    
    # ASR相关错误 2000-2999
    ASR_ENGINE_ERROR = 2000
    ASR_TRANSCRIBE_ERROR = 2001
    ASR_CONFIG_ERROR = 2002
    ASR_TIMEOUT_ERROR = 2003
    
    # TTS相关错误 3000-3999
    TTS_ENGINE_ERROR = 3000
    TTS_SYNTHESIS_ERROR = 3001
    TTS_CONFIG_ERROR = 3002
    TTS_TIMEOUT_ERROR = 3003
    
    # NLU相关错误 4000-4999
    NLU_ENGINE_ERROR = 4000
    NLU_PARSE_ERROR = 4001
    NLU_CONFIG_ERROR = 4002
    
    # AI机器人相关错误 5000-5999
    AI_ENGINE_ERROR = 5000
    AI_CHAT_ERROR = 5001
    AI_CONFIG_ERROR = 5002
    AI_QUOTA_ERROR = 5003
    
    # 服务器相关错误 6000-6999
    SERVER_ERROR = 6000
    AUTH_ERROR = 6001
    PERMISSION_ERROR = 6002
    REQUEST_ERROR = 6003
    
    # 数据库相关错误 7000-7999
    DATABASE_ERROR = 7000
    DATABASE_CONNECTION_ERROR = 7001
    DATABASE_QUERY_ERROR = 7002
    
    # 网络相关错误 8000-8999
    NETWORK_ERROR = 8000
    TIMEOUT_ERROR = 8001
    CONNECTION_ERROR = 8002
    
    # 播放器相关错误 9000-9999
    PLAYER_ERROR = 9000
    AUDIO_ERROR = 9001


class PingoBaseException(Exception):
    """Pingo系统基础异常类"""
    
    def __init__(
        self, 
        message: str,
        error_code: ErrorCode = ErrorCode.SYSTEM_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception
        self.traceback_str = traceback.format_exc() if original_exception else None
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于日志记录和API返回"""
        return {
            "error_code": self.error_code.value,
            "error_name": self.error_code.name,
            "message": self.message,
            "details": self.details,
            "traceback": self.traceback_str
        }
    
    def __str__(self) -> str:
        return f"[{self.error_code.name}] {self.message}"


class SystemException(PingoBaseException):
    """系统级异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCode.SYSTEM_ERROR, details, original_exception)


class ConfigException(PingoBaseException):
    """配置异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCode.CONFIG_ERROR, details, original_exception)


class ASRException(PingoBaseException):
    """ASR异常基类"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.ASR_ENGINE_ERROR, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, error_code, details, original_exception)


class ASRTranscribeException(ASRException):
    """ASR转录异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCode.ASR_TRANSCRIBE_ERROR, details, original_exception)


class ASRTimeoutException(ASRException):
    """ASR超时异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCode.ASR_TIMEOUT_ERROR, details, original_exception)


class TTSException(PingoBaseException):
    """TTS异常基类"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.TTS_ENGINE_ERROR, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, error_code, details, original_exception)


class TTSSynthesisException(TTSException):
    """TTS合成异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCode.TTS_SYNTHESIS_ERROR, details, original_exception)


class TTSTimeoutException(TTSException):
    """TTS超时异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCode.TTS_TIMEOUT_ERROR, details, original_exception)


class NLUException(PingoBaseException):
    """NLU异常基类"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.NLU_ENGINE_ERROR, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, error_code, details, original_exception)


class NLUParseException(NLUException):
    """NLU解析异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCode.NLU_PARSE_ERROR, details, original_exception)


class AIException(PingoBaseException):
    """AI机器人异常基类"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.AI_ENGINE_ERROR, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, error_code, details, original_exception)


class AIChatException(AIException):
    """AI聊天异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCode.AI_CHAT_ERROR, details, original_exception)


class AIQuotaException(AIException):
    """AI配额异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCode.AI_QUOTA_ERROR, details, original_exception)


class ServerException(PingoBaseException):
    """服务器异常基类"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.SERVER_ERROR, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, error_code, details, original_exception)


class AuthException(ServerException):
    """认证异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCode.AUTH_ERROR, details, original_exception)


class DatabaseException(PingoBaseException):
    """数据库异常基类"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.DATABASE_ERROR, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, error_code, details, original_exception)


class DatabaseConnectionException(DatabaseException):
    """数据库连接异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCode.DATABASE_CONNECTION_ERROR, details, original_exception)


class NetworkException(PingoBaseException):
    """网络异常基类"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.NETWORK_ERROR, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, error_code, details, original_exception)


class TimeoutException(NetworkException):
    """超时异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCode.TIMEOUT_ERROR, details, original_exception)


class PlayerException(PingoBaseException):
    """播放器异常基类"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.PLAYER_ERROR, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, error_code, details, original_exception)


class AudioException(PlayerException):
    """音频异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCode.AUDIO_ERROR, details, original_exception)