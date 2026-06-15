@echo off
REM 后台启动 MediaPilot 服务（最小化窗口）

cd /d "%~dp0"

REM 启动后端
start /min cmd /c "cd backend && python main.py > ..\logs\backend.log 2>&1"

REM 等待后端启动
timeout /t 2 /nobreak >nul

REM 启动前端
start /min cmd /c "cd web && npm run dev > ..\logs\frontend.log 2>&1"
