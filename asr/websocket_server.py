"""
FunASR WebSocket服务器
支持实时语音识别
"""

import asyncio
import json
import logging
import base64
import numpy as np
import soundfile as sf
import tempfile
import os
from typing import Dict, Any

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

from .asr_engine import asr_engine

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建WebSocket路由
ws_router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections[websocket] = {
            "session_id": len(self.active_connections),
            "connected_at": asyncio.get_event_loop().time()
        }
        logger.info(f"WebSocket连接建立，当前连接数: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            del self.active_connections[websocket]
        logger.info(f"WebSocket连接断开，当前连接数: {len(self.active_connections)}")
    
    async def send_message(self, websocket: WebSocket, message: dict):
        """发送消息到WebSocket"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {str(e)}")
    
    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        for websocket in self.active_connections:
            await self.send_message(websocket, message)


# 全局连接管理器
manager = ConnectionManager()


@ws_router.websocket("/asr/ws")
async def websocket_asr_endpoint(websocket: WebSocket):
    """
    WebSocket语音识别端点
    
    消息格式:
    {
        "type": "audio_data",
        "data": "base64编码的音频数据",
        "format": "wav",
        "sample_rate": 16000
    }
    
    或:
    {
        "type": "config",
        "load_model": true
    }
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "config":
                # 处理配置消息
                await handle_config_message(websocket, message)
                
            elif message_type == "audio_data":
                # 处理音频数据
                await handle_audio_data(websocket, message)
                
            else:
                await manager.send_message(websocket, {
                    "type": "error",
                    "message": f"未知消息类型: {message_type}"
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket连接断开")
    except Exception as e:
        logger.error(f"WebSocket处理错误: {str(e)}")
        await manager.send_message(websocket, {
            "type": "error",
            "message": f"服务器错误: {str(e)}"
        })
    finally:
        manager.disconnect(websocket)


async def handle_config_message(websocket: WebSocket, message: dict):
    """处理配置消息"""
    try:
        if message.get("load_model"):
            # 加载模型
            def load_model_sync():
                return asr_engine.load_model()
            
            success = await asyncio.get_event_loop().run_in_executor(None, load_model_sync)
            
            await manager.send_message(websocket, {
                "type": "config_response",
                "model_loaded": success,
                "message": "模型加载成功" if success else "模型加载失败"
            })
        
        elif message.get("unload_model"):
            # 卸载模型
            asr_engine.unload_model()
            await manager.send_message(websocket, {
                "type": "config_response",
                "model_loaded": False,
                "message": "模型已卸载"
            })
        
        elif message.get("get_info"):
            # 获取模型信息
            info = asr_engine.get_model_info()
            await manager.send_message(websocket, {
                "type": "info_response",
                **info
            })
            
    except Exception as e:
        await manager.send_message(websocket, {
            "type": "error",
            "message": f"配置处理失败: {str(e)}"
        })


async def handle_audio_data(websocket: WebSocket, message: dict):
    """处理音频数据"""
    try:
        # 检查模型是否加载
        if not asr_engine.is_loaded:
            await manager.send_message(websocket, {
                "type": "error",
                "message": "ASR模型未加载，请先加载模型"
            })
            return
        
        # 解码音频数据
        audio_data_b64 = message.get("data")
        if not audio_data_b64:
            await manager.send_message(websocket, {
                "type": "error",
                "message": "缺少音频数据"
            })
            return
        
        # Base64解码
        audio_bytes = base64.b64decode(audio_data_b64)
        
        # 获取音频参数
        audio_format = message.get("format", "wav")
        sample_rate = message.get("sample_rate", 16000)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(audio_bytes)
        
        try:
            # 在线程池中执行识别
            def recognize_sync():
                return asr_engine.recognize_audio_file(temp_path)
            
            result = await asyncio.get_event_loop().run_in_executor(None, recognize_sync)
            
            # 发送识别结果
            await manager.send_message(websocket, {
                "type": "recognition_result",
                **result
            })
            
        finally:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"处理音频数据失败: {str(e)}")
        await manager.send_message(websocket, {
            "type": "error",
            "message": f"音频识别失败: {str(e)}"
        })


# 为了向后兼容，也创建一个REST API路由
websocket_router = APIRouter()
websocket_router.include_router(ws_router)


@websocket_router.get("/asr/ws/status")
async def get_websocket_status():
    """获取WebSocket服务状态"""
    return {
        "status": "running",
        "active_connections": len(manager.active_connections),
        "model_loaded": asr_engine.is_loaded
    } 