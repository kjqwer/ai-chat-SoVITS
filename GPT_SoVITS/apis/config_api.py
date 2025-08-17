"""
配置管理API
处理推理配置和AI配置的管理
"""

import os
import json
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Pydantic模型
class InferenceConfigUpdate(BaseModel):
    text_lang: Optional[str] = None
    prompt_lang: Optional[str] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    temperature: Optional[float] = None
    text_split_method: Optional[str] = None
    batch_size: Optional[int] = None
    speed_factor: Optional[float] = None
    ref_text_free: Optional[bool] = None
    split_bucket: Optional[bool] = None
    fragment_interval: Optional[float] = None
    parallel_infer: Optional[bool] = None
    repetition_penalty: Optional[float] = None
    sample_steps: Optional[int] = None
    super_sampling: Optional[bool] = None

def create_config_router(app_state, dist_path):
    """创建配置管理路由器"""
    router = APIRouter(prefix="/config", tags=["config"])
    
    @router.get("/inference")
    async def get_inference_config():
        """获取当前推理配置"""
        return app_state.inference_config

    @router.post("/inference")
    async def update_inference_config(config: InferenceConfigUpdate):
        """更新推理配置"""
        for key, value in config.dict(exclude_unset=True).items():
            if hasattr(app_state.inference_config, key) or key in app_state.inference_config:
                app_state.inference_config[key] = value
        
        return {"message": "Inference config updated", "config": app_state.inference_config}
    
    return router

def create_api_config_router(dist_path):
    """创建API配置路由器"""
    router = APIRouter(prefix="/api", tags=["api-config"])
    
    @router.post("/save-config")
    async def save_config(request: dict):
        """保存AI配置到public目录"""
        try:
            config_path = os.path.join(dist_path, "ai-config.json")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # 保存配置
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(request, f, ensure_ascii=False, indent=2)
            
            return {"message": "配置保存成功", "path": config_path}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")

    @router.get("/get-config")
    async def get_config():
        """获取AI配置"""
        try:
            config_path = os.path.join(dist_path, "ai-config.json")
            
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                return config
            else:
                # 如果配置文件不存在，返回默认配置
                default_config = {
                    "API_CONFIGS": [{
                        "name": "默认OpenAI配置",
                        "baseURL": "https://api.openai.com/v1",
                        "apiKey": "your-openai-api-key",
                        "model": "gpt-3.5-turbo",
                        "timeout": 30000,
                        "isDefault": True,
                        "defaultParams": {
                            "temperature": 0.7,
                            "max_tokens": 1000,
                            "top_p": 1,
                            "frequency_penalty": 0,
                            "presence_penalty": 0
                        }
                    }],
                    "DEFAULT_PERSONAS": [{
                        "id": "assistant",
                        "name": "智能助手",
                        "description": "友善、专业的AI助手",
                        "prompt": "你是一个友善、专业且富有知识的AI助手。请用清晰、有帮助的方式回答用户的问题。保持礼貌和耐心，如果不确定答案，请诚实说明。"
                    }]
                }
                return default_config
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")
    
    return router 