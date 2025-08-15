"""
FunASR语音识别引擎 (兼容版本) 
支持Silero VAD语音活动检测
"""

import os
import logging
import tempfile
import numpy as np
import soundfile as sf
from typing import Optional, Union, Dict, Any, List
from pathlib import Path

from .model_manager import model_manager
from .config import ASRConfig

# VAD 集成
try:
    from .vad_engine import SileroVAD, vad_engine
    VAD_AVAILABLE = True
    logging.info("✅ Silero VAD可用")
except ImportError as e:
    VAD_AVAILABLE = False
    logging.warning(f"⚠️ Silero VAD不可用: {e}")

# 兼容性检查
try:
    from funasr import AutoModel
    FUNASR_AVAILABLE = True
    logging.info("✅ FunASR可用")
except ImportError:
    FUNASR_AVAILABLE = False
    logging.warning("⚠️ FunASR不可用，ASR功能将受限")


class ASREngine:
    """FunASR语音识别引擎，集成Silero VAD"""
    
    def __init__(self, 
                 model_name: str = "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                 config: Optional[ASRConfig] = None):
        """
        初始化ASR引擎
        
        Args:
            model_name: FunASR模型名称
            config: ASR配置对象
        """
        self.model_name = model_name
        self.model = None
        self.is_loaded = False
        self.logger = logging.getLogger(__name__)
        
        # 配置管理
        self.config = config or ASRConfig()
        self.vad_config = self.config.get("vad", {})
        
        # VAD集成
        self.vad_enabled = self.vad_config.get("enabled", False) and VAD_AVAILABLE
        self.vad_engine = None
        
        if self.vad_enabled:
            try:
                # 创建VAD实例
                self.vad_engine = SileroVAD(
                    model_type=self.vad_config.get("model_type", "silero_vad"),
                    device=self.vad_config.get("device", "auto")
                )
                self.logger.info("✅ VAD引擎初始化成功")
            except Exception as e:
                self.logger.warning(f"VAD引擎初始化失败: {e}")
                self.vad_enabled = False
        
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
            
            # 获取模型配置
            model_config = self.config.get("model", {})
            vad_model = model_config.get("vad_model", "fsmn-vad")
            punc_model = model_config.get("punc_model", "ct-punc")
            spk_model = model_config.get("spk_model", "cam++")
            
            # 转换所有模型路径为本地路径（如果存在）
            if vad_model and vad_model.startswith("iic/"):
                vad_model = model_manager.get_model_path_for_funasr(vad_model)
            if punc_model and punc_model.startswith("iic/"):
                punc_model = model_manager.get_model_path_for_funasr(punc_model)
            if spk_model and spk_model.startswith("iic/"):
                spk_model = model_manager.get_model_path_for_funasr(spk_model)
            
            # 显示模型路径信息
            self.logger.info(f"模型路径配置:")
            self.logger.info(f"  主模型: {model_path}")
            self.logger.info(f"  VAD模型: {vad_model}")
            self.logger.info(f"  标点模型: {punc_model}")
            self.logger.info(f"  说话人模型: {spk_model}")
            
            # 尝试加载模型的优先级策略
            loading_strategies = [
                {
                    "name": "推荐配置（含标点，无说话人）",
                    "config": {
                        "model": model_path,
                        "vad_model": vad_model,
                        "punc_model": punc_model,
                        "spk_model": None,  # 默认跳过说话人模型
                        "disable_update": True,
                        "device": "cpu"
                    }
                },
                {
                    "name": "仅标点模型（不含VAD）",
                    "config": {
                        "model": model_path,
                        "vad_model": None,
                        "punc_model": punc_model,
                        "spk_model": None,
                        "disable_update": True,
                        "device": "cpu"
                    }
                },
                {
                    "name": "使用本地标点模型路径",
                    "config": {
                        "model": model_path,
                        "vad_model": None,
                        "punc_model": model_manager.get_model_path_for_funasr("iic/punc_ct-transformer_cn-en-common-vocab471067-large"),
                        "spk_model": None,
                        "disable_update": True,
                        "device": "cpu"
                    }
                },
                {
                    "name": "完整配置（包含说话人模型）",
                    "config": {
                        "model": model_path,
                        "vad_model": vad_model,
                        "punc_model": punc_model,
                        "spk_model": spk_model,
                        "disable_update": True,
                        "device": "cpu"
                    }
                },
                {
                    "name": "简化配置（无标点，最后选择）",
                    "config": {
                        "model": model_path,
                        "disable_update": True,
                        "device": "cpu"
                    }
                }
            ]
            
            # 按优先级尝试加载
            for strategy in loading_strategies:
                try:
                    self.logger.info(f"尝试使用策略: {strategy['name']}")
                    self.model = AutoModel(**strategy['config'])
                    self.logger.info(f"✅ {strategy['name']} 加载成功")
                    
                    # 检查是否包含标点模型
                    has_punc = strategy['config'].get('punc_model') is not None
                    if has_punc:
                        self.logger.info("🔤 标点符号模型已加载，支持标点生成")
                    else:
                        self.logger.warning("⚠️ 未加载标点模型，识别结果可能无标点符号")
                    
                    break
                    
                except Exception as e:
                    self.logger.warning(f"❌ {strategy['name']} 失败: {e}")
                    continue
            else:
                # 所有策略都失败，尝试最基础的降级加载
                self.logger.info("所有预定义策略失败，尝试最终降级...")
                self.model = AutoModel(model=self.model_name)
                self.logger.warning("⚠️ 使用最基础配置，功能可能受限")
            
            self.is_loaded = True
            self.logger.info("ASR模型加载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"加载ASR模型失败: {str(e)}")
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
            
            # VAD预处理（如果启用）
            vad_segments = None
            if self.vad_enabled and self.vad_config.get("pre_process", False):
                vad_segments = self._process_with_vad(audio_path)
                if vad_segments:
                    self.logger.info(f"VAD检测到 {len(vad_segments)} 个语音片段")
            
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
    
    def _process_with_vad(self, audio_path: Union[str, Path]) -> Optional[List[Dict[str, Any]]]:
        """
        使用VAD处理音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            Optional[List[Dict]]: VAD检测的语音片段，如果失败返回None
        """
        try:
            if not self.vad_enabled or not self.vad_engine:
                return None
            
            # 获取VAD参数
            vad_params = {
                "threshold": self.vad_config.get("threshold", 0.5),
                "min_speech_duration_ms": self.vad_config.get("min_speech_duration_ms", 250),
                "max_speech_duration_s": self.vad_config.get("max_speech_duration_s", 30.0),
                "min_silence_duration_ms": self.vad_config.get("min_silence_duration_ms", 100),
                "speech_pad_ms": self.vad_config.get("speech_pad_ms", 30),
            }
            
            # 使用VAD检测语音片段
            segments = self.vad_engine.process_audio_file(audio_path, **vad_params)
            
            if segments:
                self.logger.info(f"VAD检测完成，发现 {len(segments)} 个语音片段")
                for i, segment in enumerate(segments):
                    duration = segment['end'] - segment['start']
                    self.logger.debug(f"片段 {i+1}: {segment['start']:.2f}s - {segment['end']:.2f}s (时长: {duration:.2f}s)")
            
            return segments
            
        except Exception as e:
            self.logger.error(f"VAD处理失败: {str(e)}")
            return None
    
    def recognize_with_vad(self, audio_path: Union[str, Path]) -> Dict[str, Any]:
        """
        使用VAD分段进行语音识别
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            Dict: 识别结果，包含VAD分段信息
        """
        try:
            if not self.vad_enabled:
                self.logger.warning("VAD未启用，使用常规识别")
                return self.recognize_audio_file(audio_path)
            
            # 首先进行VAD检测
            vad_segments = self._process_with_vad(audio_path)
            
            if not vad_segments:
                self.logger.warning("VAD未检测到语音片段，使用常规识别")
                return self.recognize_audio_file(audio_path)
            
            # 为每个语音片段进行识别
            all_text = []
            detailed_results = []
            total_confidence = 0.0
            
            for i, segment in enumerate(vad_segments):
                try:
                    # 创建临时音频片段文件
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                        temp_path = temp_file.name
                    
                    # 提取音频片段
                    audio_data, sr = sf.read(str(audio_path))
                    start_sample = int(segment['start'] * sr)
                    end_sample = int(segment['end'] * sr)
                    segment_audio = audio_data[start_sample:end_sample]
                    
                    # 保存片段
                    sf.write(temp_path, segment_audio, sr)
                    
                    # 识别片段
                    segment_result = self.recognize_audio_file(temp_path)
                    
                    # 清理临时文件
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                    
                    if segment_result.get("success", False):
                        text = segment_result.get("text", "").strip()
                        if text:
                            all_text.append(text)
                            total_confidence += segment_result.get("confidence", 0.0)
                            
                            detailed_results.append({
                                "segment_id": i + 1,
                                "start": segment['start'],
                                "end": segment['end'],
                                "duration": segment['duration'],
                                "text": text,
                                "confidence": segment_result.get("confidence", 0.0)
                            })
                    
                except Exception as e:
                    self.logger.warning(f"处理VAD片段 {i+1} 失败: {str(e)}")
                    continue
            
            # 合并结果
            final_text = " ".join(all_text)
            avg_confidence = total_confidence / len(detailed_results) if detailed_results else 0.0
            
            result = {
                "success": True,
                "text": final_text,
                "confidence": avg_confidence,
                "vad_segments": len(vad_segments),
                "recognized_segments": len(detailed_results),
                "detailed_results": detailed_results if self.vad_config.get("return_segments", False) else None,
                "processing_method": "vad_segmented"
            }
            
            self.logger.info(f"VAD分段识别完成: {len(detailed_results)}/{len(vad_segments)} 个片段识别成功")
            return result
            
        except Exception as e:
            self.logger.error(f"VAD分段识别失败: {str(e)}")
            # 降级到常规识别
            return self.recognize_audio_file(audio_path)
    
    def split_audio_by_vad(self, 
                          audio_path: Union[str, Path], 
                          output_dir: Union[str, Path]) -> List[str]:
        """
        使用VAD分割音频文件
        
        Args:
            audio_path: 输入音频文件路径
            output_dir: 输出目录
            
        Returns:
            List[str]: 分割后的音频文件路径列表
        """
        try:
            if not self.vad_enabled or not self.vad_engine:
                self.logger.error("VAD未启用或不可用")
                return []
            
            # 获取VAD参数
            vad_params = {
                "threshold": self.vad_config.get("threshold", 0.5),
                "min_speech_duration_ms": self.vad_config.get("min_speech_duration_ms", 250),
                "max_speech_duration_s": self.vad_config.get("max_speech_duration_s", 30.0),
                "min_silence_duration_ms": self.vad_config.get("min_silence_duration_ms", 100),
                "speech_pad_ms": self.vad_config.get("speech_pad_ms", 30),
            }
            
            return self.vad_engine.split_audio_by_vad(audio_path, output_dir, **vad_params)
            
        except Exception as e:
            self.logger.error(f"VAD音频分割失败: {str(e)}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict: 模型信息
        """
        # 检查是否有标点模型的相关属性或配置
        has_punctuation = False
        punctuation_model = None
        
        if self.is_loaded and self.model:
            # 检查模型配置
            model_config = self.config.get("model", {})
            punctuation_model = model_config.get("punc_model")
            
            # 如果配置中有标点模型，认为支持标点
            if punctuation_model and punctuation_model != "None":
                has_punctuation = True
            
            # 尝试检查模型对象本身是否有标点功能
            try:
                if hasattr(self.model, 'punc_model') and self.model.punc_model is not None:
                    has_punctuation = True
                elif hasattr(self.model, 'models') and 'punc' in str(self.model.models):
                    has_punctuation = True
            except:
                pass
        
        return {
            "model_name": self.model_name,
            "is_loaded": self.is_loaded,
            "funasr_available": FUNASR_AVAILABLE,
            "vad_enabled": self.vad_enabled,
            "vad_available": VAD_AVAILABLE,
            "vad_config": self.vad_config if self.vad_enabled else None,
            "punctuation_supported": has_punctuation,
            "punctuation_model": punctuation_model,
        }
    
    def check_punctuation_support(self) -> Dict[str, Any]:
        """
        专门检查标点符号支持情况
        
        Returns:
            Dict: 标点支持信息
        """
        if not self.is_loaded:
            return {
                "supported": False,
                "reason": "模型未加载",
                "model_loaded": False
            }
        
        model_config = self.config.get("model", {})
        punc_model = model_config.get("punc_model")
        
        if not punc_model or punc_model == "None":
            return {
                "supported": False,
                "reason": "配置中未指定标点模型",
                "model_loaded": True,
                "config_punc_model": None
            }
        
        try:
            # 尝试检查模型是否实际加载了标点功能
            has_punc_attr = hasattr(self.model, 'punc_model')
            punc_model_value = getattr(self.model, 'punc_model', None) if has_punc_attr else None
            
            return {
                "supported": True,
                "reason": "标点模型已配置",
                "model_loaded": True,
                "config_punc_model": punc_model,
                "has_punc_attribute": has_punc_attr,
                "punc_model_loaded": punc_model_value is not None if has_punc_attr else "unknown"
            }
        except Exception as e:
            return {
                "supported": False,
                "reason": f"检查标点模型时出错: {str(e)}",
                "model_loaded": True,
                "config_punc_model": punc_model
            }


# 全局ASR引擎实例
asr_engine = ASREngine() 