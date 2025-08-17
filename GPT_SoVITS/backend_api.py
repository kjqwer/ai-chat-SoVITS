import os
import json
import sys
import logging
import tempfile
import atexit
import shutil
from pathlib import Path

import torch
import psutil
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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

# 导入API模块
from apis.character_utils import load_character_data, get_default_happy_audio
from apis.models_api import create_models_router
from apis.characters_api import create_characters_router
from apis.tts_api import create_tts_router
from apis.config_api import create_config_router, create_api_config_router
from apis.status_api import create_status_router
from apis.frontend_api import create_frontend_router
from apis.conversations_api import create_conversations_router

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

# 集成ASR模块
try:
    # 确保ASR模块在Python路径中
    asr_path = os.path.join(now_dir, "asr")
    if asr_path not in sys.path:
        sys.path.insert(0, now_dir)
    
    print(f"尝试从路径加载ASR模块: {asr_path}")
    
    # 检查ASR目录是否存在
    if not os.path.exists(asr_path):
        raise ImportError(f"ASR目录不存在: {asr_path}")
    
    # 检查关键文件是否存在
    asr_api_file = os.path.join(asr_path, "asr_api.py")
    if not os.path.exists(asr_api_file):
        raise ImportError(f"asr_api.py文件不存在: {asr_api_file}")
    
    from asr import asr_router
    from asr.websocket_server import websocket_router
    from asr.asr_engine import asr_engine
    
    app.include_router(asr_router)
    app.include_router(websocket_router)
    print("✅ ASR语音识别模块已加载")
    print(f"   - ASR REST API路由已注册")
    print(f"   - ASR WebSocket路由已注册")
    
except ImportError as e:
    print(f"⚠️ ASR模块导入失败: {e}")
    print("   请确保已安装FunASR依赖: runtime\\python.exe asr/install_runtime.py")
    print(f"   ASR模块路径: {os.path.join(now_dir, 'asr')}")
except Exception as e:
    print(f"❌ ASR模块加载错误: {e}")
    import traceback
    traceback.print_exc()

# 添加静态文件服务
dist_path = os.path.join(now_dir, "ui", "dist")
if os.path.exists(dist_path):
    # 挂载静态文件目录
    app.mount("/static", StaticFiles(directory=dist_path), name="static")
    print(f"前端静态文件目录: {dist_path}")
else:
    print(f"前端静态文件目录不存在: {dist_path}")
    print("请先构建前端项目: cd ui && pnpm build")

# 注册API路由
# 模型管理API
models_router = create_models_router(
    app_state, SoVITS_names, name2sovits_path, tts_pipeline, 
    get_sovits_version_from_path_fast, dict_language_v1, dict_language_v2
)
app.include_router(models_router)

# 角色管理API
characters_router = create_characters_router(app_state, character_data, get_default_happy_audio)
app.include_router(characters_router)

# TTS API
tts_router = create_tts_router(app_state, tts_pipeline, cut_method, temp_dir)
app.include_router(tts_router)

# 配置管理API
config_router = create_config_router(app_state, dist_path)
app.include_router(config_router)

# API配置API
api_config_router = create_api_config_router(dist_path)
app.include_router(api_config_router)

# 状态API
status_router = create_status_router(app_state, device, version, model_version, temp_dir)
app.include_router(status_router)

# 对话管理API
conversations_router = create_conversations_router()
app.include_router(conversations_router)

# 前端服务API（放在最后，避免路由冲突）
frontend_router = create_frontend_router(dist_path)
app.include_router(frontend_router)

# 清理函数
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
    
    # 预加载ASR模型（在服务启动前）
    asr_preload = os.environ.get("ASR_PRELOAD", "true").lower() == "true"
    if asr_preload:
        try:
            from asr.asr_engine import asr_engine
            print("🔄 正在预加载ASR模型...")
            
            success = asr_engine.load_model()
            if success:
                print("✅ ASR模型预加载成功")
                # 检查标点支持
                punc_status = asr_engine.check_punctuation_support()
                if punc_status.get("supported"):
                    print("🔤 标点符号功能已就绪")
                else:
                    print(f"⚠️ 标点符号功能: {punc_status.get('reason', '未知')}")
            else:
                print("⚠️ ASR模型预加载失败，将在首次使用时加载")
        except Exception as e:
            print(f"⚠️ ASR模型预加载出错: {e}")
    else:
        print("⚠️ ASR预加载已禁用，首次识别时将加载模型")
        print("   提示：设置环境变量 ASR_PRELOAD=true 可启用预加载")
    
    print(f"📡 API服务地址: http://localhost:8000")
    print(f"📚 API文档地址: http://localhost:8000/docs")
    if os.path.exists(dist_path):
        print(f"🎨 前端界面地址: http://localhost:8000")
    else:
        print(f"⚠️  前端未构建，请运行: cd ui && pnpm build")
    print("="*60)
    print("按 Ctrl+C 停止服务\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)