"""
FunASR语音识别模块
提供语音到文本的转换功能
"""

from .asr_engine import ASREngine
from .asr_api import router as asr_router

__all__ = ['ASREngine', 'asr_router'] 