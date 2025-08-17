import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

# 数据模型
class Message(BaseModel):
    id: str
    role: str
    content: str
    timestamp: datetime
    audioVersions: List[Dict[str, Any]] = []
    currentAudioVersion: int = -1
    audioGenerating: bool = False

class Persona(BaseModel):
    name: str
    prompt: str
    description: Optional[str] = None

class Conversation(BaseModel):
    id: str
    title: str
    persona: Persona
    messages: List[Message] = []
    createdAt: datetime
    updatedAt: datetime

class ConversationCreate(BaseModel):
    title: str
    persona: Persona

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    persona: Optional[Persona] = None

class MessageCreate(BaseModel):
    role: str
    content: str

class AudioVersionCreate(BaseModel):
    audio_file_path: str
    is_default: bool = False

def create_conversations_router(data_dir: str = None):
    """创建对话管理API路由"""
    
    if data_dir is None:
        data_dir = os.path.join(os.getcwd(), "data", "conversations")
    
    # 确保数据目录存在
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, "audio"), exist_ok=True)
    
    router = APIRouter(prefix="/api/conversations", tags=["conversations"])
    
    def get_conversation_file_path(conversation_id: str) -> str:
        """获取对话文件路径"""
        return os.path.join(data_dir, f"{conversation_id}.json")
    
    def get_audio_file_path(conversation_id: str, message_id: str, version_id: str) -> str:
        """获取音频文件路径"""
        return os.path.join(data_dir, "audio", f"{conversation_id}_{message_id}_{version_id}.wav")
    
    def load_conversation(conversation_id: str) -> Optional[Conversation]:
        """加载对话数据"""
        file_path = get_conversation_file_path(conversation_id)
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Conversation(**data)
        except Exception as e:
            print(f"加载对话失败: {e}")
            return None
    
    def save_conversation(conversation: Conversation):
        """保存对话数据"""
        file_path = get_conversation_file_path(conversation.id)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation.dict(), f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"保存对话失败: {e}")
            raise HTTPException(status_code=500, detail="保存对话失败")
    
    def list_conversation_files() -> List[str]:
        """列出所有对话文件"""
        files = []
        for file in os.listdir(data_dir):
            if file.endswith('.json'):
                files.append(file[:-5])  # 移除.json后缀
        return files
    
    @router.get("/", response_model=List[Conversation])
    async def get_conversations():
        """获取所有对话列表"""
        try:
            conversations = []
            for conv_id in list_conversation_files():
                conversation = load_conversation(conv_id)
                if conversation:
                    conversations.append(conversation)
            
            # 按更新时间排序，最新的在前
            conversations.sort(key=lambda x: x.updatedAt, reverse=True)
            return conversations
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取对话列表失败: {str(e)}")
    
    @router.get("/{conversation_id}", response_model=Conversation)
    async def get_conversation(conversation_id: str):
        """获取单个对话"""
        conversation = load_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        return conversation
    
    @router.post("/", response_model=Conversation)
    async def create_conversation(conversation_data: ConversationCreate):
        """创建新对话"""
        try:
            conversation_id = str(int(datetime.now().timestamp() * 1000))
            conversation = Conversation(
                id=conversation_id,
                title=conversation_data.title,
                persona=conversation_data.persona,
                messages=[],
                createdAt=datetime.now(),
                updatedAt=datetime.now()
            )
            
            save_conversation(conversation)
            return conversation
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"创建对话失败: {str(e)}")
    
    @router.put("/{conversation_id}", response_model=Conversation)
    async def update_conversation(conversation_id: str, update_data: ConversationUpdate):
        """更新对话信息"""
        conversation = load_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        try:
            if update_data.title is not None:
                conversation.title = update_data.title
            if update_data.persona is not None:
                conversation.persona = update_data.persona
            
            conversation.updatedAt = datetime.now()
            save_conversation(conversation)
            return conversation
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"更新对话失败: {str(e)}")
    
    @router.delete("/{conversation_id}")
    async def delete_conversation(conversation_id: str):
        """删除对话"""
        conversation = load_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        try:
            # 删除对话文件
            file_path = get_conversation_file_path(conversation_id)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 删除相关的音频文件
            audio_dir = os.path.join(data_dir, "audio")
            for file in os.listdir(audio_dir):
                if file.startswith(f"{conversation_id}_"):
                    os.remove(os.path.join(audio_dir, file))
            
            return {"message": "对话已删除"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除对话失败: {str(e)}")
    
    @router.post("/{conversation_id}/messages", response_model=Message)
    async def add_message(conversation_id: str, message_data: MessageCreate):
        """添加消息到对话"""
        conversation = load_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        try:
            message = Message(
                id=str(int(datetime.now().timestamp() * 1000)),
                role=message_data.role,
                content=message_data.content,
                timestamp=datetime.now(),
                audioVersions=[],
                currentAudioVersion=-1,
                audioGenerating=False
            )
            
            conversation.messages.append(message)
            conversation.updatedAt = datetime.now()
            save_conversation(conversation)
            return message
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"添加消息失败: {str(e)}")
    
    @router.put("/{conversation_id}/messages/{message_id}", response_model=Message)
    async def update_message(conversation_id: str, message_id: str, message_data: MessageCreate):
        """更新消息"""
        conversation = load_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        message = next((msg for msg in conversation.messages if msg.id == message_id), None)
        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")
        
        try:
            message.role = message_data.role
            message.content = message_data.content
            conversation.updatedAt = datetime.now()
            save_conversation(conversation)
            return message
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"更新消息失败: {str(e)}")
    
    @router.delete("/{conversation_id}/messages/{message_id}")
    async def delete_message(conversation_id: str, message_id: str):
        """删除消息"""
        conversation = load_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        message = next((msg for msg in conversation.messages if msg.id == message_id), None)
        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")
        
        try:
            # 删除相关的音频文件
            audio_dir = os.path.join(data_dir, "audio")
            for file in os.listdir(audio_dir):
                if file.startswith(f"{conversation_id}_{message_id}_"):
                    os.remove(os.path.join(audio_dir, file))
            
            # 从对话中删除消息
            conversation.messages = [msg for msg in conversation.messages if msg.id != message_id]
            conversation.updatedAt = datetime.now()
            save_conversation(conversation)
            
            return {"message": "消息已删除"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除消息失败: {str(e)}")
    
    @router.post("/{conversation_id}/messages/{message_id}/audio")
    async def upload_audio(
        conversation_id: str, 
        message_id: str, 
        audio_file: UploadFile = File(...),
        is_default: bool = Form(False)
    ):
        """上传音频文件到消息"""
        conversation = load_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        message = next((msg for msg in conversation.messages if msg.id == message_id), None)
        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")
        
        try:
            # 生成版本ID
            version_id = str(int(datetime.now().timestamp() * 1000))
            audio_path = get_audio_file_path(conversation_id, message_id, version_id)
            
            # 保存音频文件
            with open(audio_path, "wb") as f:
                shutil.copyfileobj(audio_file.file, f)
            
            # 创建音频版本记录
            audio_version = {
                "id": version_id,
                "url": f"/api/conversations/{conversation_id}/messages/{message_id}/audio/{version_id}",
                "timestamp": datetime.now().isoformat(),
                "isDefault": is_default
            }
            
            # 添加到消息的音频版本列表
            message.audioVersions.append(audio_version)
            
            # 如果是默认版本或第一个版本，设置为当前版本
            if is_default or len(message.audioVersions) == 1:
                message.currentAudioVersion = len(message.audioVersions) - 1
            
            conversation.updatedAt = datetime.now()
            save_conversation(conversation)
            
            return audio_version
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"上传音频失败: {str(e)}")
    
    @router.get("/{conversation_id}/messages/{message_id}/audio/{version_id}")
    async def get_audio_file(conversation_id: str, message_id: str, version_id: str):
        """获取音频文件"""
        audio_path = get_audio_file_path(conversation_id, message_id, version_id)
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        return FileResponse(audio_path, media_type="audio/wav")
    
    @router.delete("/{conversation_id}/messages/{message_id}/audio/{version_id}")
    async def delete_audio_version(conversation_id: str, message_id: str, version_id: str):
        """删除音频版本"""
        conversation = load_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        message = next((msg for msg in conversation.messages if msg.id == message_id), None)
        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")
        
        try:
            # 找到音频版本
            version_index = next((i for i, v in enumerate(message.audioVersions) if v["id"] == version_id), None)
            if version_index is None:
                raise HTTPException(status_code=404, detail="音频版本不存在")
            
            # 删除音频文件
            audio_path = get_audio_file_path(conversation_id, message_id, version_id)
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            # 从消息中删除版本
            message.audioVersions.pop(version_index)
            
            # 调整当前版本索引
            if message.currentAudioVersion >= version_index:
                message.currentAudioVersion = max(0, message.currentAudioVersion - 1)
            if len(message.audioVersions) == 0:
                message.currentAudioVersion = -1
            
            conversation.updatedAt = datetime.now()
            save_conversation(conversation)
            
            return {"message": "音频版本已删除"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除音频版本失败: {str(e)}")
    
    @router.put("/{conversation_id}/messages/{message_id}/audio/current")
    async def set_current_audio_version(conversation_id: str, message_id: str, version_index: int):
        """设置当前音频版本"""
        conversation = load_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        message = next((msg for msg in conversation.messages if msg.id == message_id), None)
        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")
        
        if version_index < 0 or version_index >= len(message.audioVersions):
            raise HTTPException(status_code=400, detail="无效的版本索引")
        
        try:
            message.currentAudioVersion = version_index
            conversation.updatedAt = datetime.now()
            save_conversation(conversation)
            return {"message": "当前音频版本已设置"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"设置音频版本失败: {str(e)}")
    
    @router.post("/{conversation_id}/rollback/{message_index}")
    async def rollback_to_message(conversation_id: str, message_index: int):
        """回溯到指定消息"""
        conversation = load_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        if message_index < 0 or message_index >= len(conversation.messages):
            raise HTTPException(status_code=400, detail="无效的消息索引")
        
        try:
            # 删除指定索引之后的所有消息
            messages_to_delete = conversation.messages[message_index + 1:]
            
            # 删除相关音频文件
            audio_dir = os.path.join(data_dir, "audio")
            for message in messages_to_delete:
                for file in os.listdir(audio_dir):
                    if file.startswith(f"{conversation_id}_{message.id}_"):
                        os.remove(os.path.join(audio_dir, file))
            
            # 保留到指定索引的消息
            conversation.messages = conversation.messages[:message_index + 1]
            conversation.updatedAt = datetime.now()
            save_conversation(conversation)
            
            return {"message": f"已回溯到第 {message_index + 1} 条消息"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"回溯失败: {str(e)}")
    
    return router 