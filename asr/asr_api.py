"""
FunASR API路由
提供语音识别的HTTP接口
"""

import os
import logging
import tempfile
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

import soundfile as sf
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .asr_engine import asr_engine
from .model_manager import model_manager

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建API路由
router = APIRouter(prefix="/asr", tags=["语音识别"])


class ASRResponse(BaseModel):
    """ASR识别响应模型"""
    success: bool
    text: str
    confidence: Optional[float] = None
    segments: Optional[list] = None
    speaker_info: Optional[Any] = None
    timestamp: Optional[list] = None
    error: Optional[str] = None


class ModelInfo(BaseModel):
    """模型信息响应模型"""
    model_name: str
    is_loaded: bool
    funasr_available: bool


@router.get("/model/info", response_model=ModelInfo)
async def get_model_info():
    """获取ASR模型信息"""
    try:
        info = asr_engine.get_model_info()
        return ModelInfo(**info)
    except Exception as e:
        logger.error(f"获取模型信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模型信息失败: {str(e)}")


@router.post("/model/load")
async def load_model():
    """加载ASR模型"""
    try:
        def load_sync():
            return asr_engine.load_model()
        
        # 在线程池中执行模型加载
        success = await asyncio.get_event_loop().run_in_executor(None, load_sync)
        
        if success:
            return {"success": True, "message": "模型加载成功"}
        else:
            raise HTTPException(status_code=500, detail="模型加载失败")
            
    except Exception as e:
        logger.error(f"加载模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"加载模型失败: {str(e)}")


@router.post("/model/unload")
async def unload_model():
    """卸载ASR模型"""
    try:
        asr_engine.unload_model()
        return {"success": True, "message": "模型已卸载"}
    except Exception as e:
        logger.error(f"卸载模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"卸载模型失败: {str(e)}")


@router.post("/recognize/file", response_model=ASRResponse)
async def recognize_audio_file(
    audio_file: UploadFile = File(..., description="音频文件")
):
    """
    识别上传的音频文件
    支持的格式: wav, mp3, m4a, flac, aac
    """
    try:
        # 检查文件类型
        allowed_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg', '.webm'}
        file_extension = Path(audio_file.filename).suffix.lower()
        
        # 处理特殊格式映射
        if file_extension == '.mp4':
            # 将.mp4映射为.m4a，因为内容通常相同
            file_extension = '.m4a'
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的音频格式: {file_extension}. 支持的格式: {', '.join(sorted(allowed_extensions))}"
            )
        
        # 创建临时文件，使用映射后的扩展名
        temp_suffix = file_extension
        with tempfile.NamedTemporaryFile(suffix=temp_suffix, delete=False) as temp_file:
            temp_path = temp_file.name
            
            # 保存上传的文件
            content = await audio_file.read()
            temp_file.write(content)
            
        logger.info(f"临时文件已创建: {temp_path}, 原始格式: {Path(audio_file.filename).suffix}, 处理格式: {file_extension}")
        
        try:
            # 在线程池中执行识别
            def recognize_sync():
                return asr_engine.recognize_audio_file(temp_path)
            
            result = await asyncio.get_event_loop().run_in_executor(None, recognize_sync)
            
            # 删除临时文件
            os.unlink(temp_path)
            
            return ASRResponse(**result)
            
        except Exception as e:
            # 确保删除临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"识别音频文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


@router.post("/recognize/url", response_model=ASRResponse)
async def recognize_audio_url(
    url: str = Form(..., description="音频文件URL")
):
    """识别网络音频文件"""
    try:
        import requests
        
        # 下载音频文件
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 从URL获取文件扩展名
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        file_extension = Path(parsed_url.path).suffix.lower()
        
        if not file_extension:
            file_extension = '.wav'  # 默认扩展名
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(response.content)
        
        try:
            # 在线程池中执行识别
            def recognize_sync():
                return asr_engine.recognize_audio_file(temp_path)
            
            result = await asyncio.get_event_loop().run_in_executor(None, recognize_sync)
            
            # 删除临时文件
            os.unlink(temp_path)
            
            return ASRResponse(**result)
            
        except Exception as e:
            # 确保删除临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
            
    except Exception as e:
        logger.error(f"识别网络音频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "FunASR语音识别服务",
        "model_loaded": asr_engine.is_loaded
    }


@router.get("/supported_formats")
async def get_supported_formats():
    """获取支持的音频格式"""
    return {
        "formats": [".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg"],
        "description": "支持的音频文件格式"
    }


@router.get("/models/status")
async def get_models_status():
    """获取所有模型的状态"""
    try:
        return model_manager.list_models()
    except Exception as e:
        logger.error(f"获取模型状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模型状态失败: {str(e)}")


@router.post("/models/migrate")
async def migrate_models(copy_mode: bool = True):
    """
    迁移模型到本地目录
    
    Args:
        copy_mode: True为复制模式（保留缓存），False为移动模式（删除缓存）
    """
    try:
        def migrate_sync():
            return model_manager.migrate_all_models(copy_mode=copy_mode)
        
        # 在线程池中执行迁移
        results = await asyncio.get_event_loop().run_in_executor(None, migrate_sync)
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        return {
            "success": True,
            "message": f"模型迁移完成：{success_count}/{total_count} 成功",
            "mode": "复制模式" if copy_mode else "移动模式",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"模型迁移失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"模型迁移失败: {str(e)}")


@router.post("/models/clean_cache")
async def clean_cache_models():
    """清理缓存中的模型（在本地模型存在的情况下）"""
    try:
        def clean_sync():
            return model_manager.clean_cache_models()
        
        # 在线程池中执行清理
        success = await asyncio.get_event_loop().run_in_executor(None, clean_sync)
        
        if success:
            return {"success": True, "message": "缓存清理完成"}
        else:
            raise HTTPException(status_code=500, detail="缓存清理失败")
            
    except Exception as e:
        logger.error(f"清理缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")


@router.get("/models/config")
async def get_model_config():
    """获取模型配置"""
    try:
        config = model_manager.load_model_config()
        return config
    except Exception as e:
        logger.error(f"获取模型配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模型配置失败: {str(e)}") 