"""
FunASR API路由
提供语音识别的HTTP接口，集成Silero VAD功能
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
    # VAD相关字段
    vad_segments: Optional[int] = None
    recognized_segments: Optional[int] = None
    detailed_results: Optional[list] = None
    processing_method: Optional[str] = None


class VADResponse(BaseModel):
    """VAD检测响应模型"""
    success: bool
    segments: Optional[list] = None
    total_segments: Optional[int] = None
    total_speech_duration: Optional[float] = None
    error: Optional[str] = None


class ModelInfo(BaseModel):
    """模型信息响应模型"""
    model_name: str
    is_loaded: bool
    funasr_available: bool
    vad_enabled: Optional[bool] = None
    vad_available: Optional[bool] = None
    vad_config: Optional[dict] = None


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


@router.get("/model/punctuation/check")
async def check_punctuation_support():
    """检查当前模型是否支持标点符号生成"""
    try:
        result = asr_engine.check_punctuation_support()
        return result
    except Exception as e:
        logger.error(f"检查标点支持失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检查标点支持失败: {str(e)}")


@router.post("/model/reload-with-punctuation")
async def reload_model_with_punctuation():
    """重新加载模型，强制启用标点功能"""
    try:
        def reload_sync():
            # 先卸载当前模型
            asr_engine.unload_model()
            
            # 临时修改配置，确保标点模型被加载
            model_config = asr_engine.config.get("model", {})
            if not model_config.get("punc_model"):
                model_config["punc_model"] = "iic/punc_ct-transformer_cn-en-common-vocab471067-large"
                asr_engine.config.config["model"] = model_config
            
            # 重新加载模型
            return asr_engine.load_model()
        
        # 在线程池中执行模型重载
        success = await asyncio.get_event_loop().run_in_executor(None, reload_sync)
        
        if success:
            # 检查标点支持情况
            punc_status = asr_engine.check_punctuation_support()
            return {
                "success": True, 
                "message": "模型重载成功",
                "punctuation_status": punc_status
            }
        else:
            raise HTTPException(status_code=500, detail="模型重载失败")
            
    except Exception as e:
        logger.error(f"重载模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重载模型失败: {str(e)}")


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


# ======================
# VAD 相关接口
# ======================

@router.post("/vad/detect", response_model=VADResponse)
async def detect_speech_segments(
    file: UploadFile = File(..., description="音频文件"),
    threshold: Optional[float] = Form(0.5, description="语音检测阈值 (0-1)"),
    min_speech_duration_ms: Optional[int] = Form(250, description="最小语音时长(毫秒)"),
    max_speech_duration_s: Optional[float] = Form(30.0, description="最大语音时长(秒)"),
    min_silence_duration_ms: Optional[int] = Form(100, description="最小静音时长(毫秒)"),
    speech_pad_ms: Optional[int] = Form(30, description="语音片段填充时长(毫秒)")
):
    """
    使用VAD检测音频中的语音片段
    """
    if not asr_engine.vad_enabled:
        raise HTTPException(status_code=503, detail="VAD功能未启用")
    
    # 检查文件格式
    if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg')):
        raise HTTPException(status_code=400, detail="不支持的音频格式")
    
    temp_file = None
    try:
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            temp_file = tmp.name
            content = await file.read()
            tmp.write(content)
        
        # VAD参数
        vad_params = {
            "threshold": threshold,
            "min_speech_duration_ms": min_speech_duration_ms,
            "max_speech_duration_s": max_speech_duration_s,
            "min_silence_duration_ms": min_silence_duration_ms,
            "speech_pad_ms": speech_pad_ms,
        }
        
        # 检测语音片段
        segments = asr_engine._process_with_vad(temp_file)
        
        if segments is None:
            return VADResponse(
                success=False,
                error="VAD检测失败"
            )
        
        # 计算总的语音时长
        total_speech_duration = sum(seg['duration'] for seg in segments)
        
        return VADResponse(
            success=True,
            segments=segments,
            total_segments=len(segments),
            total_speech_duration=total_speech_duration
        )
        
    except Exception as e:
        logger.error(f"VAD检测失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"VAD检测失败: {str(e)}")
    
    finally:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass


@router.post("/recognize/vad", response_model=ASRResponse)
async def recognize_with_vad(
    file: UploadFile = File(..., description="音频文件"),
    return_segments: Optional[bool] = Form(False, description="是否返回详细的VAD分段信息")
):
    """
    使用VAD分段进行语音识别
    
    先使用VAD检测语音片段，然后对每个片段进行语音识别，最后合并结果
    """
    if not asr_engine.vad_enabled:
        raise HTTPException(status_code=503, detail="VAD功能未启用")
    
    # 检查文件格式
    if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg')):
        raise HTTPException(status_code=400, detail="不支持的音频格式")
    
    temp_file = None
    try:
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            temp_file = tmp.name
            content = await file.read()
            tmp.write(content)
        
        # 临时更新返回分段设置
        original_return_segments = asr_engine.vad_config.get("return_segments", False)
        asr_engine.vad_config["return_segments"] = return_segments
        
        try:
            # 使用VAD分段识别
            result = asr_engine.recognize_with_vad(temp_file)
            
            return ASRResponse(
                success=result.get("success", False),
                text=result.get("text", ""),
                confidence=result.get("confidence"),
                error=result.get("error"),
                vad_segments=result.get("vad_segments"),
                recognized_segments=result.get("recognized_segments"),
                detailed_results=result.get("detailed_results"),
                processing_method=result.get("processing_method", "vad_segmented")
            )
            
        finally:
            # 恢复原始设置
            asr_engine.vad_config["return_segments"] = original_return_segments
        
    except Exception as e:
        logger.error(f"VAD分段识别失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"VAD分段识别失败: {str(e)}")
    
    finally:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass


@router.post("/vad/split")
async def split_audio_by_vad(
    file: UploadFile = File(..., description="音频文件"),
    output_format: Optional[str] = Form("wav", description="输出格式 (wav, mp3, flac)")
):
    """
    使用VAD分割音频文件
    
    返回分割后的音频文件列表（需要额外实现文件下载接口）
    """
    if not asr_engine.vad_enabled:
        raise HTTPException(status_code=503, detail="VAD功能未启用")
    
    # 检查文件格式
    if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg')):
        raise HTTPException(status_code=400, detail="不支持的音频格式")
    
    temp_file = None
    output_dir = None
    try:
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            temp_file = tmp.name
            content = await file.read()
            tmp.write(content)
        
        # 创建输出目录
        output_dir = tempfile.mkdtemp(prefix="vad_split_")
        
        # 分割音频
        split_files = asr_engine.split_audio_by_vad(temp_file, output_dir)
        
        if not split_files:
            return {
                "success": False,
                "error": "未检测到语音片段或分割失败"
            }
        
        # 返回分割结果信息
        file_info = []
        for i, file_path in enumerate(split_files):
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_info.append({
                "segment_id": i + 1,
                "filename": file_name,
                "file_size": file_size,
                "file_path": file_path  # 注意：实际应用中不应该暴露完整路径
            })
        
        return {
            "success": True,
            "total_segments": len(split_files),
            "output_directory": output_dir,
            "files": file_info,
            "message": f"音频已分割为 {len(split_files)} 个片段"
        }
        
    except Exception as e:
        logger.error(f"VAD音频分割失败: {str(e)}")
        # 清理输出目录
        if output_dir and os.path.exists(output_dir):
            import shutil
            try:
                shutil.rmtree(output_dir)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"VAD音频分割失败: {str(e)}")
    
    finally:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass


@router.get("/vad/health")
async def vad_health_check():
    """VAD健康检查"""
    try:
        if not asr_engine.vad_enabled:
            return {
                "status": "disabled",
                "message": "VAD功能已禁用"
            }
        
        if not asr_engine.vad_engine:
            return {
                "status": "error",
                "message": "VAD引擎未初始化"
            }
        
        # 获取VAD模型信息
        model_info = asr_engine.vad_engine.get_silero_model_info()
        
        return {
            "status": "healthy" if asr_engine.vad_engine.is_loaded else "not_loaded",
            "message": "VAD功能正常" if asr_engine.vad_engine.is_loaded else "VAD模型未加载",
            "model_info": model_info
        }
        
    except Exception as e:
        logger.error(f"VAD健康检查失败: {str(e)}")
        return {
            "status": "error",
            "message": f"VAD健康检查失败: {str(e)}"
        }


@router.get("/vad/model/info")
async def get_vad_model_info():
    """获取VAD模型信息"""
    try:
        if not asr_engine.vad_enabled or not asr_engine.vad_engine:
            return {
                "available": False,
                "message": "VAD功能未启用"
            }
        
        info = asr_engine.vad_engine.get_silero_model_info()
        return {
            "available": True,
            **info
        }
        
    except Exception as e:
        logger.error(f"获取VAD模型信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取VAD模型信息失败: {str(e)}")


@router.post("/vad/model/copy-to-local")
async def copy_vad_model_to_local():
    """将VAD模型复制到本地目录"""
    try:
        if not asr_engine.vad_enabled or not asr_engine.vad_engine:
            raise HTTPException(status_code=400, detail="VAD功能未启用")
        
        def copy_sync():
            return asr_engine.vad_engine.copy_silero_to_local()
        
        # 在线程池中执行复制操作
        success = await asyncio.get_event_loop().run_in_executor(None, copy_sync)
        
        if success:
            # 获取更新后的模型信息
            model_info = asr_engine.vad_engine.get_silero_model_info()
            return {
                "success": True,
                "message": "VAD模型已复制到本地",
                "model_info": model_info
            }
        else:
            raise HTTPException(status_code=500, detail="复制VAD模型失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"复制VAD模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"复制VAD模型失败: {str(e)}") 