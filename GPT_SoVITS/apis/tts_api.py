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
    
    return router 