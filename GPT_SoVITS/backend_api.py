import os
import json
import random
import sys
import logging
import tempfile
import time
from typing import Optional, List, Dict, Any
from pathlib import Path

import torch
import psutil
import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 设置高优先级
def set_high_priority():
    """把当前 Python 进程设为 HIGH_PRIORITY_CLASS"""
    if os.name != "nt":
        return # 仅 Windows 有效
    p = psutil.Process(os.getpid())
    try:
        p.nice(psutil.HIGH_PRIORITY_CLASS)
        print("已将进程优先级设为 High")
    except psutil.AccessDenied:
        print("权限不足，无法修改优先级（请用管理员运行）")

set_high_priority()

# 添加路径
now_dir = os.getcwd()
sys.path.append(now_dir)
sys.path.append("%s/GPT_SoVITS" % (now_dir))

# 设置日志级别
logging.getLogger("markdown_it").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("charset_normalizer").setLevel(logging.ERROR)
logging.getLogger("torchaudio._extension").setLevel(logging.ERROR)

# 环境变量设置
if "_CUDA_VISIBLE_DEVICES" in os.environ:
    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ["_CUDA_VISIBLE_DEVICES"]

is_half = eval(os.environ.get("is_half", "True")) and torch.cuda.is_available()
version = model_version = os.environ.get("version", "v2")

# 导入TTS相关模块
from TTS_infer_pack.TTS import TTS, TTS_Config
from config import get_weights_names, name2sovits_path, name2gpt_path
from process_ckpt import get_sovits_version_from_path_fast
from tools.i18n.i18n import I18nAuto, scan_language_list

# 初始化i18n
language = os.environ.get("language", "Auto")
language = sys.argv[-1] if sys.argv[-1] in scan_language_list() else language
i18n = I18nAuto(language=language)

# 设备检测
if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

# 语言配置
dict_language_v1 = {
    "中文": "all_zh",
    "英文": "en",
    "日文": "all_ja",
    "中英混合": "zh",
    "日英混合": "ja",
    "多语种混合": "auto",
}
dict_language_v2 = {
    "中文": "all_zh",
    "英文": "en",
    "日文": "all_ja",
    "粤语": "all_yue",
    "韩文": "all_ko",
    "中英混合": "zh",
    "日英混合": "ja",
    "粤英混合": "yue",
    "韩英混合": "ko",
    "多语种混合": "auto",
    "多语种混合(粤语)": "auto_yue",
}

# 切分方法
cut_method = {
    "不切": "cut0",
    "凑四句一切": "cut1",
    "凑50字一切": "cut2",
    "按中文句号。切": "cut3",
    "按英文句号.切": "cut4",
    "按标点符号切": "cut5",
}

# 获取模型列表
SoVITS_names, GPT_names = get_weights_names()

# 初始化TTS配置
tts_config = TTS_Config("GPT_SoVITS/configs/tts_infer.yaml")
tts_config.device = device
tts_config.is_half = is_half
tts_config.update_version(version)

# 加载权重配置
if os.path.exists("./weight.json"):
    with open("./weight.json", "r", encoding="utf-8") as file:
        weight_data = json.loads(file.read())
        gpt_path = weight_data.get("GPT", {}).get(version, GPT_names[-1] if GPT_names else None)
        sovits_path = weight_data.get("SoVITS", {}).get(version, SoVITS_names[0] if SoVITS_names else None)
else:
    with open("./weight.json", "w", encoding="utf-8") as file:
        json.dump({"GPT": {}, "SoVITS": {}}, file)
    gpt_path = GPT_names[-1] if GPT_names else None
    sovits_path = SoVITS_names[0] if SoVITS_names else None

if gpt_path and isinstance(gpt_path, list):
    gpt_path = gpt_path[0]
if sovits_path and isinstance(sovits_path, list):
    sovits_path = sovits_path[0]

# 设置模型路径
if gpt_path:
    if "！" in gpt_path or "!" in gpt_path:
        gpt_path = name2gpt_path[gpt_path]
    tts_config.t2s_weights_path = gpt_path

if sovits_path:
    if "！" in sovits_path or "!" in sovits_path:
        sovits_path = name2sovits_path[sovits_path]
    tts_config.vits_weights_path = sovits_path

# 初始化TTS管道
tts_pipeline = TTS(tts_config)

# 角色数据加载
def load_character_data():
    """加载所有角色的音频数据"""
    character_data = {}
    reference_audios_path = "reference_audios"
    
    if not os.path.exists(reference_audios_path):
        return character_data
    
    # 加载emotions目录
    emotions_path = os.path.join(reference_audios_path, "emotions")
    if os.path.exists(emotions_path):
        for character_name in os.listdir(emotions_path):
            character_dir = os.path.join(emotions_path, character_name)
            if os.path.isdir(character_dir):
                if character_name not in character_data:
                    character_data[character_name] = {"emotions": {}, "randoms": {}}
                
                # 遍历语言目录
                for lang_dir in os.listdir(character_dir):
                    lang_path = os.path.join(character_dir, lang_dir)
                    if os.path.isdir(lang_path):
                        character_data[character_name]["emotions"][lang_dir] = []
                        
                        # 加载音频文件
                        for audio_file in os.listdir(lang_path):
                            if audio_file.endswith('.wav'):
                                # 从文件名提取情感和文本
                                import re
                                match = re.match(r'【(.+?)】(.+)\.wav', audio_file)
                                if match:
                                    emotion = match.group(1)
                                    text = match.group(2)
                                    audio_path = os.path.join(lang_path, audio_file)
                                    character_data[character_name]["emotions"][lang_dir].append({
                                        "emotion": emotion,
                                        "text": text,
                                        "path": audio_path,
                                    })
    
    # 加载randoms目录
    randoms_path = os.path.join(reference_audios_path, "randoms")
    if os.path.exists(randoms_path):
        for character_name in os.listdir(randoms_path):
            character_dir = os.path.join(randoms_path, character_name)
            if os.path.isdir(character_dir):
                if character_name not in character_data:
                    character_data[character_name] = {"emotions": {}, "randoms": {}}
                
                # 遍历语言目录
                for lang_dir in os.listdir(character_dir):
                    lang_path = os.path.join(character_dir, lang_dir)
                    if os.path.isdir(lang_path):
                        character_data[character_name]["randoms"][lang_dir] = []
                        
                        # 加载音频和lab文件对
                        wav_files = [f for f in os.listdir(lang_path) if f.endswith('.wav')]
                        for wav_file in wav_files:
                            lab_file = wav_file.replace('.wav', '.lab')
                            lab_path = os.path.join(lang_path, lab_file)
                            wav_path = os.path.join(lang_path, wav_file)
                            
                            if os.path.exists(lab_path):
                                try:
                                    with open(lab_path, 'r', encoding='utf-8') as f:
                                        text = f.read().strip()
                                    
                                    character_data[character_name]["randoms"][lang_dir].append({
                                        "text": text,
                                        "path": wav_path,
                                    })
                                except Exception as e:
                                    print(f"Error reading lab file {lab_path}: {e}")
    
    return character_data

def get_default_happy_audio(character_name, character_data, language="中文"):
    """获取角色的默认开心音频"""
    if character_name in character_data and language in character_data[character_name]["emotions"]:
        for audio_info in character_data[character_name]["emotions"][language]:
            if "开心" in audio_info["emotion"] or "happy" in audio_info["emotion"]:
                return audio_info
        # 如果没有开心音频，返回第一个emotions音频
        if character_data[character_name]["emotions"][language]:
            return character_data[character_name]["emotions"][language][0]
    
    # 如果emotions中没有音频，尝试randoms
    if character_name in character_data and language in character_data[character_name]["randoms"]:
        if character_data[character_name]["randoms"][language]:
            return character_data[character_name]["randoms"][language][0]
    
    return None

# 加载角色数据
character_data = load_character_data()

# 全局状态
class AppState:
    def __init__(self):
        self.current_sovits_model = sovits_path
        self.current_character = None
        self.current_character_audio = None
        self.dict_language = dict_language_v1 if version == "v1" else dict_language_v2
        
        # 默认推理配置
        self.inference_config = {
            "text_lang": "中文",
            "prompt_lang": "中文", 
            "top_k": 5,
            "top_p": 1.0,
            "temperature": 1.0,
            "text_split_method": "凑四句一切",
            "batch_size": 20,
            "speed_factor": 1.0,
            "ref_text_free": False,
            "split_bucket": True,
            "fragment_interval": 0.3,
            "parallel_infer": True,
            "repetition_penalty": 1.35,
            "sample_steps": 32,
            "super_sampling": False,
        }

app_state = AppState()

# 创建临时文件目录
temp_dir = tempfile.mkdtemp(prefix="tts_output_")
print(f"临时文件目录: {temp_dir}")

# Pydantic模型
class SoVITSModelInfo(BaseModel):
    name: str
    path: str
    is_current: bool

class CharacterInfo(BaseModel):
    name: str
    is_current: bool

class TTSRequest(BaseModel):
    text: str

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

# FastAPI应用
app = FastAPI(title="GPT-SoVITS TTS API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境建议限制具体域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# 添加静态文件服务
dist_path = os.path.join(now_dir, "ui", "dist")
if os.path.exists(dist_path):
    # 挂载静态文件目录
    app.mount("/static", StaticFiles(directory=dist_path), name="static")
    print(f"前端静态文件目录: {dist_path}")
else:
    print(f"前端静态文件目录不存在: {dist_path}")
    print("请先构建前端项目: cd ui && pnpm build")

@app.get("/models/sovits", response_model=List[SoVITSModelInfo])
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

@app.post("/models/sovits/set")
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
        global version, model_version
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

@app.get("/characters", response_model=List[CharacterInfo])
async def get_characters():
    """获取角色列表和当前角色"""
    characters = []
    for character_name in character_data.keys():
        characters.append(CharacterInfo(
            name=character_name,
            is_current=(character_name == app_state.current_character)
        ))
    return characters

@app.post("/characters/set")
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

@app.post("/tts")
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

@app.get("/config/inference")
async def get_inference_config():
    """获取当前推理配置"""
    return app_state.inference_config

@app.post("/config/inference")
async def update_inference_config(config: InferenceConfigUpdate):
    """更新推理配置"""
    for key, value in config.dict(exclude_unset=True).items():
        if hasattr(app_state.inference_config, key) or key in app_state.inference_config:
            app_state.inference_config[key] = value
    
    return {"message": "Inference config updated", "config": app_state.inference_config}

@app.get("/status")
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

@app.post("/api/save-config")
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

# 前端路由处理
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """服务前端首页"""
    index_path = os.path.join(dist_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>前端文件未找到</h1><p>请先构建前端项目: cd ui && pnpm build</p>")

@app.get("/{path:path}", response_class=HTMLResponse)
async def serve_frontend_routes(path: str):
    """处理前端路由（SPA模式）"""
    # 检查是否是API路径
    if path.startswith("models/") or path.startswith("characters/") or path.startswith("config/") or path.startswith("tts") or path.startswith("status"):
        # 让FastAPI处理API路由
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # 检查是否是静态资源
    static_file_path = os.path.join(dist_path, path)
    if os.path.exists(static_file_path) and os.path.isfile(static_file_path):
        # 根据文件扩展名返回适当的MIME类型
        if path.endswith('.js'):
            with open(static_file_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read(), media_type="application/javascript")
        elif path.endswith('.css'):
            with open(static_file_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read(), media_type="text/css")
        elif path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico')):
            return FileResponse(static_file_path)
        else:
            with open(static_file_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    
    # 对于其他路径，返回index.html（SPA路由）
    index_path = os.path.join(dist_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>前端文件未找到</h1><p>请先构建前端项目: cd ui && pnpm build</p>")

# 清理函数
import atexit
import shutil

def cleanup_temp_files():
    """清理临时文件"""
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"已清理临时文件目录: {temp_dir}")
    except Exception as e:
        print(f"清理临时文件时出错: {e}")

atexit.register(cleanup_temp_files)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 GPT-SoVITS TTS 服务启动中...")
    print("="*60)
    print(f"📡 API服务地址: http://localhost:8000")
    print(f"📚 API文档地址: http://localhost:8000/docs")
    if os.path.exists(dist_path):
        print(f"🎨 前端界面地址: http://localhost:8000")
    else:
        print(f"⚠️  前端未构建，请运行: cd ui && pnpm build")
    print("="*60)
    print("按 Ctrl+C 停止服务\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 