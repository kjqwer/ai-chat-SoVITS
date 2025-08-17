"""
TTS API
处理文本转语音功能
"""

import os
import time
import random
import tempfile
import soundfile as sf
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Pydantic模型
class TTSRequest(BaseModel):
    text: str

class ConversationTTSRequest(BaseModel):
    text: str
    conversation_id: str
    message_id: str

def create_tts_router(app_state, tts_pipeline, cut_method, temp_dir):
    """创建TTS路由器"""
    router = APIRouter(prefix="/tts", tags=["tts"])
    
    @router.post("")
    async def text_to_speech(request: TTSRequest):
        """文本转语音"""
        if not app_state.current_character or not app_state.current_character_audio:
            raise HTTPException(status_code=400, detail="No character selected")
        
        try:
            # 准备推理参数
            seed = random.randint(0, 2**32 - 1)
            audio_info = app_state.current_character_audio
            
            inputs = {
                "text": request.text,
                "text_lang": app_state.dict_language[app_state.inference_config["text_lang"]],
                "ref_audio_path": audio_info["path"],
                "aux_ref_audio_paths": [],
                "prompt_text": audio_info["text"],
                "prompt_lang": app_state.dict_language[app_state.inference_config["prompt_lang"]],
                "top_k": app_state.inference_config["top_k"],
                "top_p": app_state.inference_config["top_p"],
                "temperature": app_state.inference_config["temperature"],
                "text_split_method": cut_method[app_state.inference_config["text_split_method"]],
                "batch_size": app_state.inference_config["batch_size"],
                "speed_factor": app_state.inference_config["speed_factor"],
                "split_bucket": app_state.inference_config["split_bucket"],
                "return_fragment": False,
                "fragment_interval": app_state.inference_config["fragment_interval"],
                "seed": seed,
                "parallel_infer": app_state.inference_config["parallel_infer"],
                "repetition_penalty": app_state.inference_config["repetition_penalty"],
                "sample_steps": app_state.inference_config["sample_steps"],
                "super_sampling": app_state.inference_config["super_sampling"],
            }
            
            # 执行推理，获取生成器结果
            for result in tts_pipeline.run(inputs):
                # result 是 (sampling_rate, audio_data) 的元组
                sampling_rate, audio_data = result
                break  # 只取第一个结果
            
            # 生成临时文件名
            timestamp = int(time.time())
            temp_filename = f"tts_output_{timestamp}_{seed}.wav"
            output_path = os.path.join(temp_dir, temp_filename)
            
            # 保存音频文件
            sf.write(output_path, audio_data, sampling_rate)
            
            return FileResponse(
                output_path,
                media_type="audio/wav",
                filename=temp_filename,
                headers={"Content-Disposition": f"attachment; filename={temp_filename}"}
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
    
    @router.post("/conversation")
    async def text_to_speech_for_conversation(request: ConversationTTSRequest):
        """为对话消息生成语音并保存到对话系统"""
        if not app_state.current_character or not app_state.current_character_audio:
            raise HTTPException(status_code=400, detail="No character selected")
        
        try:
            # 准备推理参数
            seed = random.randint(0, 2**32 - 1)
            audio_info = app_state.current_character_audio
            
            inputs = {
                "text": request.text,
                "text_lang": app_state.dict_language[app_state.inference_config["text_lang"]],
                "ref_audio_path": audio_info["path"],
                "aux_ref_audio_paths": [],
                "prompt_text": audio_info["text"],
                "prompt_lang": app_state.dict_language[app_state.inference_config["prompt_lang"]],
                "top_k": app_state.inference_config["top_k"],
                "top_p": app_state.inference_config["top_p"],
                "temperature": app_state.inference_config["temperature"],
                "text_split_method": cut_method[app_state.inference_config["text_split_method"]],
                "batch_size": app_state.inference_config["batch_size"],
                "speed_factor": app_state.inference_config["speed_factor"],
                "split_bucket": app_state.inference_config["split_bucket"],
                "return_fragment": False,
                "fragment_interval": app_state.inference_config["fragment_interval"],
                "seed": seed,
                "parallel_infer": app_state.inference_config["parallel_infer"],
                "repetition_penalty": app_state.inference_config["repetition_penalty"],
                "sample_steps": app_state.inference_config["sample_steps"],
                "super_sampling": app_state.inference_config["super_sampling"],
            }
            
            # 执行推理，获取生成器结果
            for result in tts_pipeline.run(inputs):
                # result 是 (sampling_rate, audio_data) 的元组
                sampling_rate, audio_data = result
                break  # 只取第一个结果
            
            # 生成音频文件名和版本ID
            timestamp = int(time.time())
            version_id = f"{timestamp}_{seed}"
            audio_filename = f"{request.conversation_id}_{request.message_id}_{version_id}.wav"
            
            # 保存到对话系统的音频目录
            conversations_data_dir = os.path.join(os.getcwd(), "data", "conversations", "audio")
            os.makedirs(conversations_data_dir, exist_ok=True)
            output_path = os.path.join(conversations_data_dir, audio_filename)
            
            # 保存音频文件
            sf.write(output_path, audio_data, sampling_rate)
            
            # 将音频版本信息添加到对话消息中
            import json
            from datetime import datetime
            
            # 加载对话数据
            conversation_file = os.path.join(os.getcwd(), "data", "conversations", f"{request.conversation_id}.json")
            if os.path.exists(conversation_file):
                try:
                    with open(conversation_file, 'r', encoding='utf-8') as f:
                        conversation_data = json.load(f)
                    
                    # 找到对应的消息
                    message_found = False
                    for message in conversation_data.get('messages', []):
                        if message['id'] == request.message_id:
                            # 创建音频版本记录
                            audio_version = {
                                "id": version_id,
                                "url": f"/api/conversations/{request.conversation_id}/messages/{request.message_id}/audio/{version_id}",
                                "timestamp": datetime.now().isoformat(),
                                "isDefault": len(message.get('audioVersions', [])) == 0
                            }
                            
                            # 添加到消息的音频版本列表
                            if 'audioVersions' not in message:
                                message['audioVersions'] = []
                            message['audioVersions'].append(audio_version)
                            
                            # 设置为当前版本（新生成的版本总是当前版本）
                            message['currentAudioVersion'] = len(message['audioVersions']) - 1
                            
                            message_found = True
                            break
                    
                    if message_found:
                        # 更新对话的更新时间
                        conversation_data['updatedAt'] = datetime.now().isoformat()
                        
                        # 保存更新后的对话数据
                        with open(conversation_file, 'w', encoding='utf-8') as f:
                            json.dump(conversation_data, f, ensure_ascii=False, indent=2, default=str)
                        
                        print(f"音频版本已保存到对话: {request.conversation_id}, 消息: {request.message_id}, 版本: {version_id}")
                    else:
                        print(f"未找到消息: {request.message_id}")
                        
                except Exception as e:
                    print(f"保存音频版本信息失败: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 返回音频信息
            return {
                "audio_url": f"/api/conversations/{request.conversation_id}/messages/{request.message_id}/audio/{version_id}",
                "filename": audio_filename,
                "timestamp": timestamp,
                "seed": seed,
                "version_id": version_id
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
    
    return router 