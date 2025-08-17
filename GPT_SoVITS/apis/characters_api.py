"""
角色管理API
处理角色选择和音频管理功能
"""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Pydantic模型
class CharacterInfo(BaseModel):
    name: str
    is_current: bool

def create_characters_router(app_state, character_data, get_default_happy_audio):
    """创建角色管理路由器"""
    router = APIRouter(prefix="/characters", tags=["characters"])
    
    @router.get("", response_model=List[CharacterInfo])
    async def get_characters():
        """获取角色列表和当前角色"""
        characters = []
        for character_name in character_data.keys():
            characters.append(CharacterInfo(
                name=character_name,
                is_current=(character_name == app_state.current_character)
            ))
        return characters

    @router.post("/set")
    async def set_character(character_name: str):
        """设置当前角色"""
        if character_name not in character_data:
            raise HTTPException(status_code=404, detail="Character not found")
        
        # 自动选择开心音频
        default_audio = get_default_happy_audio(character_name, character_data, "中文")
        if not default_audio:
            raise HTTPException(status_code=404, detail="No audio found for character")
        
        app_state.current_character = character_name
        app_state.current_character_audio = default_audio
        
        return {
            "message": "Character set successfully",
            "character": character_name,
            "audio_path": default_audio["path"],
            "audio_text": default_audio["text"]
        }
    
    return router 