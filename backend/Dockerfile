# MediaPilot 后端 Dockerfile
# 多阶段构建：依赖安装 → 生产运行时

# ========== 第一阶段：依赖安装 ==========
FROM python:3.11-slim as dependencies

WORKDIR /app

# 安装系统依赖（gcc 用于编译，ffmpeg 用于 Whisper）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ========== 第二阶段：生产镜像 ==========
FROM python:3.11-slim

WORKDIR /app

# 运行时环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# 安装运行时系统依赖（ffmpeg 用于 Whisper 转写）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash mediapilot
USER mediapilot

# 从依赖阶段复制已安装的包
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# 复制应用代码
COPY --chown=mediapilot:mediapilot . .

# 创建必要目录
RUN mkdir -p uploads

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# 从 backend/ 上下文构建，所以入口是 main:app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
