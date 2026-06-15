#!/bin/bash
# MediaPilot 本地开发环境启动脚本
# 同时启动前端 (5173) 和后端 (8000)

set -e

echo "========================================"
echo "MediaPilot 本地开发环境启动"
echo "========================================"

# 检查 Python
echo ""
echo "[1/3] 检查 Python 环境..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "错误: 未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo "Python: $PYTHON_VERSION"

# 检查 Node.js
echo ""
echo "[2/3] 检查 Node.js 环境..."
if ! command -v node &> /dev/null; then
    echo "错误: 未找到 Node.js，请先安装 Node.js 18+"
    exit 1
fi

NODE_VERSION=$(node --version 2>&1)
echo "Node.js: $NODE_VERSION"

# 检查依赖
echo ""
echo "[3/3] 检查依赖..."

if [ ! -f "backend/requirements.txt" ]; then
    echo "警告: 未找到 backend/requirements.txt"
else
    echo "后端依赖文件存在"
fi

if [ ! -d "web/node_modules" ]; then
    echo "警告: 未安装前端依赖，运行: cd web && npm install"
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo ""
    echo "注意: .env 文件不存在，从 .env.example 创建"
    cp .env.example .env 2>/dev/null || true
fi

echo ""
echo "========================================"
echo "启动服务..."
echo "========================================"
echo "后端: http://localhost:8000 (API 文档: /docs)"
echo "前端: http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 创建日志目录
mkdir -p logs

# 启动后端
echo "启动后端服务..."
$PYTHON_CMD backend/main.py > logs/backend.log 2>&1 &
BACKEND_PID=$!

# 启动前端
echo "启动前端服务..."
cd web && npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# 清理函数
cleanup() {
    echo ""
    echo "正在停止服务..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "服务已停止"
    exit 0
}

# 捕获 Ctrl+C
trap cleanup SIGINT SIGTERM

# 等待服务启动
sleep 3

# 显示后端日志
tail -f logs/backend.log &
TAIL_PID=$!

# 等待进程结束
wait $BACKEND_PID $FRONTEND_PID
