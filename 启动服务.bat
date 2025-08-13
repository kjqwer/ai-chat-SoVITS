@echo off
chcp 65001
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"
set "PATH=%SCRIPT_DIR%\runtime;%PATH%"

echo 正在启动 GPT-SoVITS 服务...

runtime\python.exe -I GPT_SoVITS\backend_api.py
pause 