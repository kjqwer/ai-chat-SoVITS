#!/usr/bin/env python3
"""
FunASR模型管理器
支持将模型从缓存目录移动到项目目录，并管理本地模型
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ModelManager:
    """FunASR模型管理器"""
    
    def __init__(self, project_root: Optional[str] = None):
        """
        初始化模型管理器
        
        Args:
            project_root: 项目根目录，默认为当前ASR模块的上级目录
        """
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root)
        self.models_dir = self.project_root / "asr_models"
        self.cache_dir = Path.home() / ".cache" / "modelscope" / "hub" / "iic"
        self.model_config_file = self.models_dir / "model_config.json"
        
        # 创建模型目录
        self.models_dir.mkdir(exist_ok=True)
        
        # 默认模型配置
        self.default_models = {
            "asr_model": "speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
            "vad_model": "speech_fsmn_vad_zh-cn-16k-common-pytorch", 
            "punc_model": "punc_ct-transformer_cn-en-common-vocab471067-large",
            "spk_model": "speech_campplus_sv_zh-cn_16k-common"
        }
    
    def get_cache_model_path(self, model_name: str) -> Path:
        """获取缓存中的模型路径"""
        return self.cache_dir / model_name
    
    def get_local_model_path(self, model_name: str) -> Path:
        """获取本地模型路径"""
        return self.models_dir / model_name
    
    def is_model_in_cache(self, model_name: str) -> bool:
        """检查模型是否在缓存中"""
        cache_path = self.get_cache_model_path(model_name)
        return cache_path.exists() and cache_path.is_dir()
    
    def is_model_local(self, model_name: str) -> bool:
        """检查模型是否在本地目录"""
        local_path = self.get_local_model_path(model_name)
        return local_path.exists() and local_path.is_dir()
    
    def get_model_size(self, model_path: Path) -> int:
        """获取模型目录大小（字节）"""
        total_size = 0
        if model_path.exists():
            for dirpath, dirnames, filenames in os.walk(model_path):
                for filename in filenames:
                    filepath = Path(dirpath) / filename
                    if filepath.exists():
                        total_size += filepath.stat().st_size
        return total_size
    
    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def move_model_to_local(self, model_name: str) -> bool:
        """
        将模型从缓存移动到本地目录
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 是否成功移动
        """
        try:
            cache_path = self.get_cache_model_path(model_name)
            local_path = self.get_local_model_path(model_name)
            
            if not self.is_model_in_cache(model_name):
                logger.warning(f"模型不在缓存中: {model_name}")
                return False
            
            if self.is_model_local(model_name):
                logger.info(f"模型已存在于本地: {model_name}")
                return True
            
            # 获取模型大小
            model_size = self.get_model_size(cache_path)
            logger.info(f"正在移动模型 {model_name} ({self.format_size(model_size)})...")
            
            # 移动模型文件
            shutil.move(str(cache_path), str(local_path))
            
            logger.info(f"模型移动成功: {model_name} -> {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"移动模型失败 {model_name}: {str(e)}")
            return False
    
    def copy_model_to_local(self, model_name: str) -> bool:
        """
        将模型从缓存复制到本地目录（保留缓存）
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 是否成功复制
        """
        try:
            cache_path = self.get_cache_model_path(model_name)
            local_path = self.get_local_model_path(model_name)
            
            if not self.is_model_in_cache(model_name):
                logger.warning(f"模型不在缓存中: {model_name}")
                return False
            
            if self.is_model_local(model_name):
                logger.info(f"模型已存在于本地: {model_name}")
                return True
            
            # 获取模型大小
            model_size = self.get_model_size(cache_path)
            logger.info(f"正在复制模型 {model_name} ({self.format_size(model_size)})...")
            
            # 复制模型文件
            shutil.copytree(str(cache_path), str(local_path))
            
            logger.info(f"模型复制成功: {model_name} -> {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"复制模型失败 {model_name}: {str(e)}")
            return False
    
    def migrate_all_models(self, copy_mode: bool = True) -> Dict[str, bool]:
        """
        迁移所有默认模型到本地
        
        Args:
            copy_mode: True为复制模式，False为移动模式
            
        Returns:
            Dict: 各模型的迁移结果
        """
        results = {}
        
        for model_type, model_name in self.default_models.items():
            logger.info(f"处理 {model_type}: {model_name}")
            
            if copy_mode:
                success = self.copy_model_to_local(model_name)
            else:
                success = self.move_model_to_local(model_name)
            
            results[model_name] = success
        
        # 保存配置
        self.save_model_config()
        
        return results
    
    def save_model_config(self):
        """保存模型配置到文件"""
        config = {
            "models_dir": str(self.models_dir),
            "local_models": {},
            "model_mapping": {}
        }
        
        # 扫描本地模型
        for model_name in self.default_models.values():
            local_path = self.get_local_model_path(model_name)
            if local_path.exists():
                config["local_models"][model_name] = {
                    "path": str(local_path),
                    "size": self.get_model_size(local_path),
                    "exists": True
                }
                # 创建映射，支持通过iic/模型名访问
                config["model_mapping"][f"iic/{model_name}"] = str(local_path)
        
        with open(self.model_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"模型配置已保存: {self.model_config_file}")
    
    def load_model_config(self) -> Dict:
        """加载模型配置"""
        if self.model_config_file.exists():
            with open(self.model_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get_model_path_for_funasr(self, model_name: str) -> str:
        """
        获取用于FunASR的模型路径
        优先使用本地模型，如果不存在则返回原始模型名
        
        Args:
            model_name: 模型名称（如: iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch）
            
        Returns:
            str: 模型路径或模型名
        """
        # 移除 iic/ 前缀
        clean_model_name = model_name.replace("iic/", "")
        
        local_path = self.get_local_model_path(clean_model_name)
        if local_path.exists():
            logger.info(f"使用本地模型: {local_path}")
            return str(local_path)
        else:
            logger.info(f"使用在线模型: {model_name}")
            return model_name
    
    def list_models(self) -> Dict[str, Dict]:
        """列出所有模型的状态"""
        models_status = {}
        
        for model_type, model_name in self.default_models.items():
            cache_exists = self.is_model_in_cache(model_name)
            local_exists = self.is_model_local(model_name)
            
            cache_size = 0
            local_size = 0
            
            if cache_exists:
                cache_size = self.get_model_size(self.get_cache_model_path(model_name))
            
            if local_exists:
                local_size = self.get_model_size(self.get_local_model_path(model_name))
            
            models_status[model_name] = {
                "type": model_type,
                "cache_exists": cache_exists,
                "local_exists": local_exists,
                "cache_size": self.format_size(cache_size) if cache_size > 0 else "0 B",
                "local_size": self.format_size(local_size) if local_size > 0 else "0 B",
                "cache_path": str(self.get_cache_model_path(model_name)),
                "local_path": str(self.get_local_model_path(model_name))
            }
        
        return models_status
    
    def clean_cache_models(self) -> bool:
        """清理缓存中的模型（在确认本地模型存在后）"""
        try:
            cleaned = []
            for model_name in self.default_models.values():
                if self.is_model_local(model_name) and self.is_model_in_cache(model_name):
                    cache_path = self.get_cache_model_path(model_name)
                    shutil.rmtree(cache_path)
                    cleaned.append(model_name)
                    logger.info(f"已清理缓存模型: {model_name}")
            
            if cleaned:
                logger.info(f"共清理了 {len(cleaned)} 个缓存模型")
            else:
                logger.info("没有需要清理的缓存模型")
            
            return True
            
        except Exception as e:
            logger.error(f"清理缓存模型失败: {str(e)}")
            return False


# 全局模型管理器实例
model_manager = ModelManager() 