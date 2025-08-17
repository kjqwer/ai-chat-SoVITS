"""
状态API
处理系统状态查询
"""

from fastapi import APIRouter

def create_status_router(app_state, device, version, model_version, temp_dir):
    """创建状态查询路由器"""
    router = APIRouter(prefix="/status", tags=["status"])
    
    @router.get("")
    async def get_status():
        """获取系统状态"""
        return {
            "current_sovits_model": app_state.current_sovits_model,
            "current_character": app_state.current_character,
            "current_character_audio": app_state.current_character_audio["text"] if app_state.current_character_audio else None,
            "device": device,
            "version": version,
            "model_version": model_version,
            "temp_dir": temp_dir,
        }
    
    return router 