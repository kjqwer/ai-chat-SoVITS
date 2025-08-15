@echo off
chcp 65001
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"
set "PATH=%SCRIPT_DIR%\runtime;%PATH%"

echo.
echo ======================================================
echo          GPT-SoVITS + FunASR 语音识别服务
echo ======================================================
echo.

echo 正在检查ASR模块依赖...
runtime\python.exe -c "import funasr; print('✅ FunASR已安装')" 2>nul
if errorlevel 1 (
    echo ❌ FunASR未安装，正在自动安装...
    echo.
    runtime\python.exe asr/install_runtime.py
    if errorlevel 1 (
        echo.
        echo ❌ ASR模块安装失败，将以基础模式启动服务
        echo 如需使用语音识别功能，请手动运行: runtime\python.exe asr/install_runtime.py
        echo.
        pause
    )
)

echo 正在检查VAD模块依赖...
runtime\python.exe -c "import torch; import onnxruntime; print('✅ VAD依赖已安装')" 2>nul
if errorlevel 1 (
    echo ⚠️ VAD依赖未完全安装，VAD功能可能受限
    echo 如需完整VAD功能，请确保安装: torch, onnxruntime
)

echo.
echo 正在启动服务...
echo 📡 API服务地址: http://localhost:8000
echo 📚 API文档地址: http://localhost:8000/docs
echo 🎤 ASR接口地址: http://localhost:8000/asr/health
echo 🎙️ VAD接口地址: http://localhost:8000/asr/vad/health
echo.
echo 按 Ctrl+C 停止服务
echo.

runtime\python.exe -I GPT_SoVITS\backend_api.py

pause 