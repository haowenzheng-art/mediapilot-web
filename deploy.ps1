# MediaPilot 一键部署脚本 (Windows)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "MediaPilot 部署脚本" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 检查 Docker 是否安装
$dockerInstalled = $false
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker 已安装: $dockerVersion" -ForegroundColor Green
        $dockerInstalled = $true
    }
} catch {
    $dockerInstalled = $false
}

if (-not $dockerInstalled) {
    Write-Host "❌ 错误: Docker 未安装" -ForegroundColor Red
    Write-Host "请访问 https://docs.docker.com/get-docker/ 安装 Docker" -ForegroundColor Yellow
    exit 1
}

# 检查 Docker Compose
$composeInstalled = $false
try {
    docker compose version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker Compose 已安装" -ForegroundColor Green
        $composeInstalled = $true
    }
} catch {
    $composeInstalled = $false
}

if (-not $composeInstalled) {
    try {
        docker-compose --version 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker Compose 已安装" -ForegroundColor Green
            $composeInstalled = $true
        }
    } catch {
        $composeInstalled = $false
    }
}

if (-not $composeInstalled) {
    Write-Host "❌ 错误: Docker Compose 未安装" -ForegroundColor Red
    Write-Host "请访问 https://docs.docker.com/compose/install/ 安装 Docker Compose" -ForegroundColor Yellow
    exit 1
}

# 检查 .env 文件
if (-not (Test-Path .env)) {
    Write-Host "⚠️  警告: .env 文件不存在，从 .env.example 创建" -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "请编辑 .env 文件填入实际配置，特别是 JWT_SECRET" -ForegroundColor Yellow
}

Write-Host "`n1. 停止现有服务（如果存在）..." -ForegroundColor Cyan
docker-compose down 2>&1 | Out-Null

Write-Host "2. 构建 Docker 镜像..." -ForegroundColor Cyan
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 构建失败" -ForegroundColor Red
    exit 1
}

Write-Host "3. 启动服务..." -ForegroundColor Cyan
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 启动失败" -ForegroundColor Red
    exit 1
}

Write-Host "4. 等待服务启动..." -ForegroundColor Cyan
Start-Sleep -Seconds 15

Write-Host "5. 健康检查..." -ForegroundColor Cyan

# 检查后端
$backendHealthy = $false
try {
    $response = Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing -TimeoutSec 10 2>&1
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        if ($data.status -eq "healthy") {
            Write-Host "✅ 后端服务正常" -ForegroundColor Green
            $backendHealthy = $true
        }
    }
} catch {
    Write-Host "❌ 后端服务异常" -ForegroundColor Red
}

# 检查前端
$frontendHealthy = $false
try {
    $response = Invoke-WebRequest -Uri http://localhost:80/health -UseBasicParsing -TimeoutSec 10 2>&1
    if ($response.StatusCode -eq 200) {
        $content = $response.Content.Trim()
        if ($content -eq "healthy") {
            Write-Host "✅ 前端服务正常" -ForegroundColor Green
            $frontendHealthy = $true
        }
    }
} catch {
    Write-Host "❌ 前端服务异常" -ForegroundColor Red
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "部署完成！" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "前端地址: http://localhost" -ForegroundColor White
Write-Host "后端 API: http://localhost:8000" -ForegroundColor White
Write-Host "API 文档: http://localhost:8000/docs" -ForegroundColor White
Write-Host "`n查看日志: docker-compose logs -f" -ForegroundColor Gray
Write-Host "停止服务: docker-compose down" -ForegroundColor Gray
