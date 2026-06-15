#!/bin/bash
# MediaPilot 一键部署脚本

set -e

echo "=========================================="
echo "MediaPilot 部署脚本"
echo "=========================================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    echo "请访问 https://docs.docker.com/get-docker/ 安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "错误: Docker Compose 未安装"
    echo "请访问 https://docs.docker.com/compose/install/ 安装 Docker Compose"
    exit 1
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "警告: .env 文件不存在，从 .env.example 创建"
    cp .env.example .env
    echo "请编辑 .env 文件填入实际配置，特别是 JWT_SECRET"
fi

echo "1. 停止现有服务（如果存在）"
docker-compose down 2>/dev/null || true

echo "2. 构建 Docker 镜像"
docker-compose build

echo "3. 启动服务"
docker-compose up -d

echo "4. 等待服务启动..."
sleep 10

echo "5. 健康检查..."
BACKEND_HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo "failed")
FRONTEND_HEALTH=$(curl -s http://localhost:80/health 2>/dev/null || echo "failed")

if [ "$BACKEND_HEALTH" = '{"status":"healthy"}' ]; then
    echo "✅ 后端服务正常"
else
    echo "❌ 后端服务异常"
fi

if [ "$FRONTEND_HEALTH" = "healthy" ]; then
    echo "✅ 前端服务正常"
else
    echo "❌ 前端服务异常"
fi

echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo "前端地址: http://localhost"
echo "后端 API: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
