"""
模型管理API
处理SoVITS模型的加载、切换等功能
"""

import json
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Pydantic模型
class SoVITSModelInfo(BaseModel):
    name: str
    path: str
    is_current: bool

def create_models_router(app_state, SoVITS_names, name2sovits_path, tts_pipeline, get_sovits_version_from_path_fast, dict_language_v1, dict_language_v2):
    """创建模型管理路由器"""
    router = APIRouter(prefix="/models", tags=["models"])
    
    @router.get("/sovits", response_model=List[SoVITSModelInfo])
    async def get_sovits_models():
        """获取SoVITS模型列表和当前使用模型"""
        models = []
        for model_name in SoVITS_names:
            models.append(SoVITSModelInfo(
                name=model_name,
                path=model_name,
                is_current=(model_name == app_state.current_sovits_model)
            ))
        return models

    @router.post("/sovits/set")
    async def set_sovits_model(model_name: str):
        """设置当前SoVITS模型"""
        if model_name not in SoVITS_names:
            raise HTTPException(status_code=404, detail="Model not found")
        
        try:
            # 更新模型路径
            sovits_path = model_name
            if "！" in sovits_path or "!" in sovits_path:
                sovits_path = name2sovits_path[sovits_path]
            
            # 获取模型版本信息
            version, model_version, if_lora_v3 = get_sovits_version_from_path_fast(sovits_path)
            
            # 更新语言字典
            app_state.dict_language = dict_language_v1 if version == "v1" else dict_language_v2
            
            # 加载模型
            tts_pipeline.init_vits_weights(sovits_path)
            app_state.current_sovits_model = model_name
            
            # 保存到配置文件
            with open("./weight.json", "r") as f:
                data = json.loads(f.read())
                data["SoVITS"][version] = sovits_path
            with open("./weight.json", "w") as f:
                f.write(json.dumps(data))
            
            return {"message": "Model set successfully", "model": model_name}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to set model: {str(e)}")
    
    return router 