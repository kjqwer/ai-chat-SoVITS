"""
FunASR配置管理
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class ASRConfig:
    """ASR配置管理类"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        "model": {
            "name": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
            "vad_model": "fsmn-vad",
            "punc_model": "ct-punc", 
            "spk_model": "cam++",
            "device": "auto",  # auto, cpu, cuda
        },
        "audio": {
            "sample_rate": 16000,
            "max_duration": 300,  # 最大音频时长（秒）
            "supported_formats": [".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg"]
        },
        "api": {
            "max_file_size": 50 * 1024 * 1024,  # 50MB
            "timeout": 30,  # 超时时间（秒）
        },
        "cache": {
            "enabled": True,
            "max_size": 100,  # 最大缓存条目数
            "ttl": 3600,  # 缓存生存时间（秒）
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为 asr/config.json
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config.json"
        
        self.config_path = Path(config_path)
        self.config = self.DEFAULT_CONFIG.copy()
        
        # 加载配置文件
        self.load_config()
    
    def load_config(self):
        """从文件加载配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._merge_config(self.config, file_config)
        except Exception as e:
            print(f"加载配置文件失败: {e}, 使用默认配置")
    
    def save_config(self):
        """保存配置到文件"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def _merge_config(self, base: Dict[str, Any], update: Dict[str, Any]):
        """递归合并配置"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的路径，如 'model.name'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的路径
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.get('model', {})
    
    def get_audio_config(self) -> Dict[str, Any]:
        """获取音频配置"""
        return self.get('audio', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self.get('api', {})
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置"""
        return self.get('cache', {})
    
    def update_model_config(self, **kwargs):
        """更新模型配置"""
        for key, value in kwargs.items():
            self.set(f'model.{key}', value)
    
    def to_dict(self) -> Dict[str, Any]:
        """返回完整配置字典"""
        return self.config.copy()


# 全局配置实例
config = ASRConfig()


def get_config() -> ASRConfig:
    """获取全局配置实例"""
    return config


def reset_config():
    """重置为默认配置"""
    global config
    config.config = ASRConfig.DEFAULT_CONFIG.copy()
    config.save_config()


# 环境变量覆盖
def load_env_config():
    """从环境变量加载配置"""
    env_mapping = {
        'ASR_MODEL_NAME': 'model.name',
        'ASR_DEVICE': 'model.device',
        'ASR_SAMPLE_RATE': 'audio.sample_rate',
        'ASR_MAX_DURATION': 'audio.max_duration',
        'ASR_MAX_FILE_SIZE': 'api.max_file_size',
        'ASR_TIMEOUT': 'api.timeout',
    }
    
    for env_key, config_key in env_mapping.items():
        env_value = os.getenv(env_key)
        if env_value is not None:
            # 尝试转换为适当的类型
            try:
                if config_key.endswith(('rate', 'duration', 'size', 'timeout')):
                    env_value = int(env_value)
            except ValueError:
                pass
            
            config.set(config_key, env_value)


# 启动时加载环境变量配置
load_env_config() 