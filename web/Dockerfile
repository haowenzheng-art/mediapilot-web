# MediaPilot 前端 Dockerfile
# 多阶段构建：npm install → Vite build → Nginx 运行时

# ========== 第一阶段：构建 ==========
FROM node:20-alpine AS build

WORKDIR /app

# 安装依赖（包含 devDependencies 用于构建）
COPY package.json package-lock.json* ./
RUN npm ci

# 复制源代码并构建
COPY . .
RUN npm run build


# ========== 第二阶段：Nginx 运行时 ==========
FROM nginx:alpine

# 复制自定义 Nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 从构建阶段复制产物
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
