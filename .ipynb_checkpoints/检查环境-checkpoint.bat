
@echo off
chcp 65001 &gt;nul
title MediaPilot - 环境检查
color 0A

echo ========================================
echo    MediaPilot - 环境检查
echo ========================================
echo.

cd /d "%~dp0"

echo 正在检查Python...
python --version &gt;nul 2&gt;&amp;1
if errorlevel 1 (
    echo [错误] 未找到Python！
    echo.
    echo 请先打开 Anaconda Prompt，再运行此脚本
    echo.
    pause
    exit /b 1
)

echo [成功] Python已找到
echo.
echo 正在运行环境检查...
echo.

python 检查环境.py

pause

