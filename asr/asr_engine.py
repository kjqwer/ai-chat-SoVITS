"""
FunASR语音识别引擎 (兼容版本)
"""

import os
import logging
import tempfile
import numpy as np
import soundfile as sf
from typing import Optional, Union, Dict, Any
from pathlib import Path

from .model_manager import model_manager

# 兼容性检查
try:
    from funasr import AutoModel
    FUNASR_AVAILABLE = True
    logging.info("✅ FunASR可用")
except ImportError:
    FUNASR_AVAILABLE = False
    logging.warning("⚠️ FunASR不可用，ASR功能将受限")


class ASREngine:
    """FunASR语音识别引擎"""
    
    def __init__(self, model_name: str = "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"):
        """
        初始化ASR引擎
        
        Args:
            model_name: FunASR模型名称
        """
        self.model_name = model_name
        self.model = None
        self.is_loaded = False
        self.logger = logging.getLogger(__name__)
        
        if not FUNASR_AVAILABLE:
            self.logger.warning("FunASR不可用，部分功能将受限")
            # 不抛出异常，允许以降级模式运行
    
    def load_model(self) -> bool:
        """
        加载ASR模型
        
        Returns:
            bool: 是否加载成功
        """
        try:
            if self.is_loaded:
                return True
            
            if not FUNASR_AVAILABLE:
                self.logger.warning("FunASR不可用，无法加载模型")
                return False
                
            self.logger.info(f"正在加载ASR模型: {self.model_name}")
            
            # 获取本地模型路径（如果存在的话）
            model_path = model_manager.get_model_path_for_funasr(self.model_name)
            
            # 尝试使用简化配置加载FunASR模型
            try:
                # 方法1: 最简配置，只加载主模型
                self.model = AutoModel(
                    model=model_path,
                    disable_update=True,  # 禁用自动更新
                    device="cpu"  # 强制使用CPU避免CUDA问题
                )
                self.logger.info("使用简化配置加载模型成功")
            except Exception as e:
                self.logger.warning(f"简化配置加载失败: {e}")
                
                # 方法2: 尝试不加载说话人模型
                try:
                    self.model = AutoModel(
                        model=self.model_name,
                        vad_model="fsmn-vad",
                        punc_model="ct-punc",
                        spk_model=None,  # 不加载说话人识别模型
                        disable_update=True,
                        device="cpu"
                    )
                    self.logger.info("不加载说话人模型成功")
                except Exception as e2:
                    self.logger.warning(f"第二种方法也失败: {e2}")
                    
                    # 方法3: 最基础配置
                    self.model = AutoModel(
                        model=self.model_name,
                        vad_model=None,
                        punc_model=None,
                        spk_model=None,
                        disable_update=True,
                        device="cpu"
                    )
                    self.logger.info("使用最基础配置加载成功")
            
            self.is_loaded = True
            self.logger.info("ASR模型加载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"加载ASR模型失败: {str(e)}")
            # 尝试降级处理
            try:
                self.logger.info("尝试降级加载...")
                self.model = AutoModel(model=self.model_name)
                self.is_loaded = True
                self.logger.info("降级加载成功")
                return True
            except Exception as e2:
                self.logger.error(f"降级加载也失败: {str(e2)}")
                return False
    
    def unload_model(self):
        """卸载模型释放内存"""
        if self.model is not None:
            del self.model
            self.model = None
            self.is_loaded = False
            self.logger.info("ASR模型已卸载")
    
    def recognize_audio_file(self, audio_path: Union[str, Path]) -> Dict[str, Any]:
        """
        识别音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            Dict: 识别结果
        """
        try:
            if not FUNASR_AVAILABLE:
                return {
                    "success": False,
                    "text": "",
                    "error": "FunASR不可用，请安装FunASR"
                }
            
            if not self.is_loaded and not self.load_model():
                raise RuntimeError("ASR模型未加载")
            
            audio_path = str(audio_path)
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"音频文件不存在: {audio_path}")
            
            # 使用FunASR进行识别
            result = self.model.generate(input=audio_path)
            
            if result and len(result) > 0:
                # 提取识别结果
                recognition_result = result[0]
                
                # 处理不同的结果格式
                if isinstance(recognition_result, dict):
                    text = recognition_result.get("text", "")
                    confidence = recognition_result.get("confidence", 0.0)
                    segments = recognition_result.get("segments", [])
                    timestamp = recognition_result.get("timestamp", [])
                elif isinstance(recognition_result, str):
                    # 如果直接返回字符串
                    text = recognition_result
                    confidence = 1.0
                    segments = []
                    timestamp = []
                else:
                    # 其他格式，尝试转换为字符串
                    text = str(recognition_result)
                    confidence = 1.0
                    segments = []
                    timestamp = []
                
                # 格式化返回结果
                formatted_result = {
                    "success": True,
                    "text": text,
                    "confidence": confidence,
                    "segments": segments,
                    "speaker_info": None,  # 说话人信息可能不可用
                    "timestamp": timestamp,
                }
                
                self.logger.info(f"识别成功: {formatted_result['text']}")
                return formatted_result
            else:
                return {
                    "success": False,
                    "text": "",
                    "error": "未识别到语音内容"
                }
                
        except Exception as e:
            self.logger.error(f"语音识别失败: {str(e)}")
            return {
                "success": False,
                "text": "",
                "error": str(e)
            }
    
    def recognize_audio_data(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """
        识别音频数据
        
        Args:
            audio_data: 音频数据数组
            sample_rate: 采样率
            
        Returns:
            Dict: 识别结果
        """
        try:
            if not FUNASR_AVAILABLE:
                return {
                    "success": False,
                    "text": "",
                    "error": "FunASR不可用，请安装FunASR"
                }
            
            if not self.is_loaded and not self.load_model():
                raise RuntimeError("ASR模型未加载")
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                
                # 保存音频数据到临时文件
                sf.write(temp_path, audio_data, sample_rate)
                
                # 识别音频文件
                result = self.recognize_audio_file(temp_path)
                
                # 删除临时文件
                os.unlink(temp_path)
                
                return result
                
        except Exception as e:
            self.logger.error(f"识别音频数据失败: {str(e)}")
            return {
                "success": False,
                "text": "",
                "error": str(e)
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict: 模型信息
        """
        return {
            "model_name": self.model_name,
            "is_loaded": self.is_loaded,
            "funasr_available": FUNASR_AVAILABLE,
        }


# 全局ASR引擎实例
asr_engine = ASREngine() 