@echo off
REM MediaPilot 本地开发环境启动脚本 (Windows)
REM 同时启动前端 (5173) 和后端 (8000)

echo ========================================
echo MediaPilot 本地开发环境启动
echo ========================================

REM 检查 Python
echo.
echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo Python: %%i

REM 检查 Node.js
echo.
echo [2/3] 检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version 2^>^&1') do echo Node.js: %%i

REM 检查依赖
echo.
echo [3/3] 检查依赖...

if not exist "backend\requirements.txt" (
    echo 警告: 未找到 backend\requirements.txt
) else (
    echo 后端依赖文件存在
)

if not exist "web\node_modules" (
    echo 警告: 未安装前端依赖，运行: cd web ^&^& npm install
)

if not exist ".env" (
    echo.
    echo 注意: .env 文件不存在，从 .env.example 创建
    copy ".env.example" ".env" >nul 2>&1
)

echo.
echo ========================================
echo 启动服务...
echo ========================================
echo 后端: http://localhost:8000 (API 文档: /docs)
echo 前端: http://localhost:5173
echo.
echo 按任意键启动，Ctrl+C 停止
pause >nul

REM 创建日志目录
if not exist "logs" mkdir logs

REM 启动后端（在新窗口）
echo 启动后端服务...
start "MediaPilot Backend" cmd /k "cd /d "%~dp0backend" && python main.py"

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端（在新窗口）
echo 启动前端服务...
start "MediaPilot Frontend" cmd /k "cd /d "%~dp0web" && npm run dev"

echo.
echo 服务已在独立窗口中启动
echo 关闭对应窗口即可停止服务
pause
