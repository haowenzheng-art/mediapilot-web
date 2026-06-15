@echo off
REM 设置 Docker 容器开机自启动
REM 需要以管理员身份运行

echo ========================================
echo MediaPilot Docker 开机自启动配置
echo ========================================

REM 检查管理员权限
net session >nul 2>&1
if errorlevel 1 (
    echo 错误: 需要管理员权限运行此脚本
    echo 请右键选择"以管理员身份运行"
    pause
    exit /b 1
)

REM 检查 Docker 是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)

echo.
echo [1/2] 配置 Docker Desktop 开机启动...

REM 创建开机启动任务
schtasks /create /tn "MediaPilot-Docker-Start" /tr "docker-compose up -d" /sc onlogon /rl highest /f >nul 2>&1
if errorlevel 1 (
    echo 失败: 无法创建任务计划
) else (
    echo 成功: 已创建开机启动任务
)

echo.
echo [2/2] 启动服务...
docker-compose up -d

echo.
echo ========================================
echo 配置完成！
echo ========================================
echo.
echo 服务现在已启动，并且会在下次开机时自动启动
echo.
echo 前端: http://localhost
echo 后端: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo.
pause
