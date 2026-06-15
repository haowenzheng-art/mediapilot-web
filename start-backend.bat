@echo off
REM 单独启动后端服务

echo ========================================
echo MediaPilot 后端服务
echo ========================================
echo.
echo 地址: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

cd /d "%~dp0backend"
python main.py
