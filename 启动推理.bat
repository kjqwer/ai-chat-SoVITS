@echo off
chcp 65001
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"
set "PATH=%SCRIPT_DIR%\runtime;%PATH%"

echo 正在启动 GPT-SoVITS 推理 WebUI...
echo 推理界面将在浏览器中打开: http://localhost:9872

runtime\python.exe -I GPT_SoVITS\inference_webui_simplified.py zh_CN
pause 