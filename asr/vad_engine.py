"""
Silero VAD语音活动检测引擎
"""

import os
import logging
import tempfile
import numpy as np
import soundfile as sf
import torch
from typing import Optional, Union, Dict, Any, List, Tuple
from pathlib import Path

# VAD 相关导入
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False


class SileroVAD:
    """Silero VAD语音活动检测器"""
    
    def __init__(self, 
                 model_type: str = "silero_vad",
                 onnx_path: Optional[str] = None,
                 device: str = "auto"):
        """
        初始化VAD检测器
        
        Args:
            model_type: 模型类型，支持 "silero_vad" 或 "onnx"
            onnx_path: ONNX模型路径（如果使用ONNX）
            device: 设备类型 ("auto", "cpu", "cuda")
        """
        self.model_type = model_type
        self.onnx_path = onnx_path
        self.device = self._get_device(device)
        self.model = None
        self.utils = None
        self.onnx_session = None
        self.is_loaded = False
        self.logger = logging.getLogger(__name__)
        
        # VAD 参数
        self.sample_rate = 16000
        self.chunk_size = 1536  # silero-vad 的标准块大小
        
    def _get_device(self, device: str) -> str:
        """获取设备类型"""
        if device == "auto":
            if torch.cuda.is_available() and TORCH_AVAILABLE:
                return "cuda"
            else:
                return "cpu"
        return device
    
    def load_model(self) -> bool:
        """加载VAD模型"""
        try:
            if self.model_type == "silero_vad" and TORCH_AVAILABLE:
                self.logger.info("正在加载Silero VAD模型...")
                
                # 检查是否有本地缓存的模型
                local_model_path = self._get_local_silero_path()
                
                # 使用torch.hub加载silero-vad
                try:
                    if local_model_path and os.path.exists(local_model_path):
                        self.logger.info(f"使用本地缓存的Silero VAD模型: {local_model_path}")
                        # 尝试从本地路径加载
                        self.model, self.utils = torch.hub.load(
                            repo_or_dir=local_model_path,
                            model='silero_vad',
                            source='local',
                            force_reload=False,
                            onnx=False
                        )
                    else:
                        self.logger.info("从远程仓库加载Silero VAD模型...")
                        self.model, self.utils = torch.hub.load(
                            repo_or_dir='snakers4/silero-vad',
                            model='silero_vad',
                            force_reload=False,
                            onnx=False
                        )
                    
                    # 移动模型到指定设备
                    if self.device == "cuda" and torch.cuda.is_available():
                        try:
                            self.model = self.model.to("cuda")
                            # 确保模型处于评估模式
                            self.model.eval()
                            # 测试模型是否正确加载到GPU
                            test_input = torch.zeros(1, 1600).to("cuda")  # 0.1秒的16kHz音频
                            with torch.no_grad():
                                _ = self.model(test_input, 16000)
                            self.logger.info(f"✅ Silero VAD模型加载到GPU成功")
                        except Exception as gpu_error:
                            self.logger.warning(f"GPU加载失败，回退到CPU: {gpu_error}")
                            self.device = "cpu"
                            self.model = self.model.to("cpu")
                    else:
                        self.model = self.model.to("cpu")
                        self.device = "cpu"
                    
                    # 确保模型处于评估模式
                    self.model.eval()
                    
                    self.logger.info(f"✅ Silero VAD模型加载成功 (device: {self.device})")
                    
                except Exception as e:
                    self.logger.warning(f"从torch.hub加载失败: {e}")
                    self.logger.info("尝试加载ONNX版本作为回退...")
                    # 自动切换到ONNX模式
                    self.model_type = "onnx"
                    return self._load_onnx_model()
                    
            elif self.model_type == "onnx" or not TORCH_AVAILABLE:
                return self._load_onnx_model()
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            self.logger.error(f"VAD模型加载失败: {str(e)}")
            return False
    
    def _get_local_silero_path(self) -> Optional[str]:
        """获取本地Silero VAD模型路径"""
        try:
            # 检查常见的缓存路径
            possible_paths = [
                os.path.expanduser("~/.cache/torch/hub/snakers4_silero-vad_master"),
                os.path.expanduser("~/.cache/torch/hub/snakers4_silero-vad_main"),
                # 项目本地路径
                os.path.join(os.getcwd(), "asr_models", "silero_vad"),
                # Windows路径
                os.path.expandvars("%USERPROFILE%\\.cache\\torch\\hub\\snakers4_silero-vad_master"),
            ]
            
            for path in possible_paths:
                if os.path.exists(path) and os.path.isdir(path):
                    # 检查是否包含必要的文件
                    if os.path.exists(os.path.join(path, "hubconf.py")):
                        self.logger.info(f"找到本地Silero VAD模型: {path}")
                        return path
            
            return None
            
        except Exception as e:
            self.logger.warning(f"检查本地Silero模型路径时出错: {e}")
            return None
    
    def copy_silero_to_local(self) -> bool:
        """将Silero VAD模型复制到项目本地目录"""
        try:
            import shutil
            
            # 寻找缓存中的模型
            cache_paths = [
                os.path.expanduser("~/.cache/torch/hub/snakers4_silero-vad_master"),
                os.path.expanduser("~/.cache/torch/hub/snakers4_silero-vad_main"),
                os.path.expandvars("%USERPROFILE%\\.cache\\torch\\hub\\snakers4_silero-vad_master"),
            ]
            
            source_path = None
            for path in cache_paths:
                if os.path.exists(path) and os.path.isdir(path):
                    if os.path.exists(os.path.join(path, "hubconf.py")):
                        source_path = path
                        break
            
            if not source_path:
                self.logger.warning("未找到缓存的Silero VAD模型")
                return False
            
            # 目标路径
            target_path = os.path.join(os.getcwd(), "asr_models", "silero_vad")
            
            if os.path.exists(target_path):
                self.logger.info(f"Silero VAD模型已存在于本地: {target_path}")
                return True
            
            # 创建目标目录
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # 复制模型
            self.logger.info(f"正在复制Silero VAD模型: {source_path} -> {target_path}")
            shutil.copytree(source_path, target_path)
            
            self.logger.info(f"✅ Silero VAD模型已复制到本地: {target_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"复制Silero VAD模型失败: {str(e)}")
            return False
    
    def get_silero_model_info(self) -> Dict[str, Any]:
        """获取Silero VAD模型信息"""
        try:
            # 检查缓存路径
            cache_paths = [
                os.path.expanduser("~/.cache/torch/hub/snakers4_silero-vad_master"),
                os.path.expanduser("~/.cache/torch/hub/snakers4_silero-vad_main"),
                os.path.expandvars("%USERPROFILE%\\.cache\\torch\\hub\\snakers4_silero-vad_master"),
            ]
            
            cache_exists = False
            cache_path = None
            for path in cache_paths:
                if os.path.exists(path):
                    cache_exists = True
                    cache_path = path
                    break
            
            # 检查本地路径
            local_path = os.path.join(os.getcwd(), "asr_models", "silero_vad")
            local_exists = os.path.exists(local_path)
            
            return {
                "cache_exists": cache_exists,
                "cache_path": cache_path,
                "local_exists": local_exists,
                "local_path": local_path,
                "is_loaded": self.is_loaded,
                "current_device": self.device if self.is_loaded else None
            }
            
        except Exception as e:
            self.logger.error(f"获取Silero模型信息失败: {str(e)}")
            return {
                "cache_exists": False,
                "local_exists": False,
                "error": str(e)
            }
    
    def _load_onnx_model(self) -> bool:
        """加载ONNX模型"""
        try:
            if not ONNX_AVAILABLE:
                self.logger.error("ONNX Runtime不可用")
                return False
            
            # 如果没有指定ONNX路径，尝试从torch.hub获取
            if not self.onnx_path:
                self.logger.info("正在获取ONNX模型...")
                try:
                    _, utils = torch.hub.load(
                        repo_or_dir='snakers4/silero-vad',
                        model='silero_vad',
                        force_reload=False,
                        onnx=True
                    )
                    self.utils = utils
                    
                    # 获取ONNX模型路径
                    import torch.hub
                    hub_dir = torch.hub.get_dir()
                    onnx_path = os.path.join(hub_dir, 'snakers4_silero-vad_master', 'files', 'silero_vad.onnx')
                    
                    if os.path.exists(onnx_path):
                        self.onnx_path = onnx_path
                    else:
                        self.logger.error("未找到ONNX模型文件")
                        return False
                        
                except Exception as e:
                    self.logger.error(f"获取ONNX模型失败: {e}")
                    return False
            
            # 创建ONNX会话
            providers = ['CPUExecutionProvider']
            if self.device == "cuda" and 'CUDAExecutionProvider' in ort.get_available_providers():
                providers.insert(0, 'CUDAExecutionProvider')
            
            self.onnx_session = ort.InferenceSession(self.onnx_path, providers=providers)
            self.logger.info(f"✅ ONNX VAD模型加载成功 (providers: {providers})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"ONNX模型加载失败: {str(e)}")
            return False
    
    def detect_speech_chunks(self, 
                           audio_data: np.ndarray, 
                           threshold: float = 0.5,
                           min_speech_duration_ms: int = 250,
                           max_speech_duration_s: float = float('inf'),
                           min_silence_duration_ms: int = 100,
                           speech_pad_ms: int = 30) -> List[Dict[str, Any]]:
        """
        检测语音片段
        
        Args:
            audio_data: 音频数据 (numpy array)
            threshold: 语音检测阈值 (0-1)
            min_speech_duration_ms: 最小语音时长(毫秒)
            max_speech_duration_s: 最大语音时长(秒)
            min_silence_duration_ms: 最小静音时长(毫秒)
            speech_pad_ms: 语音片段填充时长(毫秒)
            
        Returns:
            List[Dict]: 语音片段列表，每个包含 start, end, confidence
        """
        try:
            if not self.is_loaded and not self.load_model():
                raise RuntimeError("VAD模型未加载")
            
            # 确保音频是16kHz
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)  # 转为单声道
            
            # 使用silero-vad进行检测
            if self.model_type == "silero_vad" and self.utils:
                try:
                    get_speech_timestamps = self.utils[0]
                    
                    # 转换为torch tensor并移动到正确的设备
                    audio_tensor = torch.from_numpy(audio_data).float()
                    
                    # 确保音频tensor和模型在同一设备上
                    if self.device == "cuda" and torch.cuda.is_available():
                        audio_tensor = audio_tensor.to("cuda")
                    else:
                        audio_tensor = audio_tensor.to("cpu")
                    
                    # 获取语音时间戳
                    speech_timestamps = get_speech_timestamps(
                        audio_tensor,
                        self.model,
                        threshold=threshold,
                        min_speech_duration_ms=min_speech_duration_ms,
                        max_speech_duration_s=max_speech_duration_s,
                        min_silence_duration_ms=min_silence_duration_ms,
                        speech_pad_ms=speech_pad_ms,
                        return_seconds=True
                    )
                    
                    # 格式化结果
                    segments = []
                    for segment in speech_timestamps:
                        segments.append({
                            'start': segment['start'],
                            'end': segment['end'],
                            'confidence': 1.0,  # silero-vad不提供置信度
                            'duration': segment['end'] - segment['start']
                        })
                    
                    return segments
                    
                except Exception as torch_error:
                    self.logger.error(f"PyTorch VAD处理失败: {torch_error}")
                    self.logger.info("尝试回退到ONNX模式...")
                    
                    # 尝试加载ONNX模型作为回退
                    if self._load_onnx_model():
                        self.model_type = "onnx"
                        return self._detect_with_onnx(audio_data, threshold)
                    else:
                        raise torch_error
                
            elif self.onnx_session:
                # 使用ONNX模型进行检测
                return self._detect_with_onnx(audio_data, threshold)
            
            else:
                raise RuntimeError("没有可用的VAD模型")
                
        except Exception as e:
            self.logger.error(f"语音检测失败: {str(e)}")
            return []
    
    def _detect_with_onnx(self, audio_data: np.ndarray, threshold: float) -> List[Dict[str, Any]]:
        """使用ONNX模型进行检测"""
        try:
            segments = []
            chunk_size = self.chunk_size
            sample_rate = self.sample_rate
            
            # 初始化状态
            h = np.zeros((2, 1, 64), dtype=np.float32)
            c = np.zeros((2, 1, 64), dtype=np.float32)
            
            # 分块处理
            speech_probs = []
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                
                # 确保块大小正确
                if len(chunk) < chunk_size:
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
                
                # 准备输入
                chunk = chunk.reshape(1, -1).astype(np.float32)
                sr = np.array([sample_rate], dtype=np.int64)
                
                # 推理
                ort_inputs = {
                    'input': chunk,
                    'sr': sr,
                    'h': h,
                    'c': c
                }
                
                ort_outputs = self.onnx_session.run(None, ort_inputs)
                prob, h, c = ort_outputs
                
                speech_probs.append(prob[0][0])
            
            # 后处理：查找语音片段
            is_speech = np.array(speech_probs) > threshold
            segments = self._post_process_segments(is_speech, chunk_size, sample_rate)
            
            return segments
            
        except Exception as e:
            self.logger.error(f"ONNX检测失败: {str(e)}")
            return []
    
    def _post_process_segments(self, is_speech: np.ndarray, chunk_size: int, sample_rate: int) -> List[Dict[str, Any]]:
        """后处理语音片段"""
        segments = []
        
        # 查找连续的语音区域
        speech_starts = []
        speech_ends = []
        
        in_speech = False
        for i, speech in enumerate(is_speech):
            if speech and not in_speech:
                speech_starts.append(i)
                in_speech = True
            elif not speech and in_speech:
                speech_ends.append(i)
                in_speech = False
        
        # 处理最后一个片段
        if in_speech:
            speech_ends.append(len(is_speech))
        
        # 转换为时间戳
        chunk_duration = chunk_size / sample_rate
        
        for start_idx, end_idx in zip(speech_starts, speech_ends):
            start_time = start_idx * chunk_duration
            end_time = end_idx * chunk_duration
            
            segments.append({
                'start': start_time,
                'end': end_time,
                'confidence': 1.0,
                'duration': end_time - start_time
            })
        
        return segments
    
    def process_audio_file(self, 
                          audio_path: Union[str, Path],
                          **kwargs) -> List[Dict[str, Any]]:
        """
        处理音频文件，检测语音片段
        
        Args:
            audio_path: 音频文件路径
            **kwargs: VAD参数
            
        Returns:
            List[Dict]: 语音片段列表
        """
        try:
            # 读取音频文件
            audio_data, sr = sf.read(str(audio_path))
            
            # 重采样到16kHz（如果需要）
            if sr != self.sample_rate:
                self.logger.info(f"重采样音频从 {sr}Hz 到 {self.sample_rate}Hz")
                import librosa
                audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
            
            # 检测语音片段
            return self.detect_speech_chunks(audio_data, **kwargs)
            
        except Exception as e:
            self.logger.error(f"处理音频文件失败: {str(e)}")
            return []
    
    def split_audio_by_vad(self, 
                          audio_path: Union[str, Path],
                          output_dir: Union[str, Path],
                          **kwargs) -> List[str]:
        """
        根据VAD结果分割音频文件
        
        Args:
            audio_path: 输入音频文件路径
            output_dir: 输出目录
            **kwargs: VAD参数
            
        Returns:
            List[str]: 分割后的音频文件路径列表
        """
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 读取音频
            audio_data, sr = sf.read(str(audio_path))
            
            # 重采样到16kHz（如果需要）
            if sr != self.sample_rate:
                import librosa
                audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
                sr = self.sample_rate
            
            # 检测语音片段
            segments = self.detect_speech_chunks(audio_data, **kwargs)
            
            output_files = []
            audio_name = Path(audio_path).stem
            
            for i, segment in enumerate(segments):
                start_sample = int(segment['start'] * sr)
                end_sample = int(segment['end'] * sr)
                
                # 提取片段
                segment_audio = audio_data[start_sample:end_sample]
                
                # 保存片段
                output_file = output_dir / f"{audio_name}_segment_{i:03d}.wav"
                sf.write(output_file, segment_audio, sr)
                output_files.append(str(output_file))
            
            self.logger.info(f"音频分割完成，共生成 {len(output_files)} 个片段")
            return output_files
            
        except Exception as e:
            self.logger.error(f"音频分割失败: {str(e)}")
            return []
    
    def unload_model(self):
        """卸载模型释放内存"""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.onnx_session is not None:
            del self.onnx_session
            self.onnx_session = None
        
        self.is_loaded = False
        self.logger.info("VAD模型已卸载")


# 创建全局VAD实例
vad_engine = SileroVAD() 