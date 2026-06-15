@echo off
REM 创建 Windows 开机自启动脚本（非 Docker）
REM 需要以管理员身份运行

echo ========================================
echo MediaPilot Windows 开机自启动配置
echo ========================================

REM 检查管理员权限
net session >nul 2>&1
if errorlevel 1 (
    echo 错误: 需要管理员权限运行此脚本
    echo 请右键选择"以管理员身份运行"
    pause
    exit /b 1
)

echo.
echo 选择安装方式:
echo 1. 当前用户开机启动（推荐）
echo 2. 所有用户开机启动
echo.

set /p choice="请输入选项 (1/2): "

if "%choice%"=="1" (
    set startup_folder="%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
) else if "%choice%"=="2" (
    set startup_folder="%ProgramData%\Microsoft\Windows\Start Menu\Programs\Startup"
) else (
    echo 无效选项
    pause
    exit /b 1
)

echo.
echo 复制启动脚本到启动文件夹...

REM 创建隐藏窗口的 VBS 启动器
echo Set WshShell = CreateObject("WScript.Shell") > "%TEMP%\mediapilot_start.vbs"
echo WshShell.Run Chr(34) ^& "%~dp0start-background.bat" ^& Chr(34), 0, False >> "%TEMP%\mediapilot_start.vbs"

copy "%TEMP%\mediapilot_start.vbs" %startup_folder%\mediapilot_start.vbs >nul 2>&1

if errorlevel 1 (
    echo 失败: 无法复制到启动文件夹
) else (
    echo 成功: 已配置开机自启动
)

echo.
echo ========================================
echo 配置完成！
echo ========================================
echo.
echo 下次开机时服务将自动在后台启动
echo 访问地址: http://localhost:5173
echo.
pause
