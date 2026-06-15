@echo off
REM 单独启动前端服务

echo ========================================
echo MediaPilot 前端服务
echo ========================================
echo.
echo 地址: http://localhost:5173
echo.
echo 按 Ctrl+C 停止服务
echo.

cd /d "%~dp0web"
npm run dev
