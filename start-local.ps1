# MediaPilot 本地开发环境启动脚本
# 同时启动前端 (5173) 和后端 (8000)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MediaPilot 本地开发环境启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 检查 Python
Write-Host "`n[1/3] 检查 Python 环境..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Host "错误: 未找到 Python，请先安装 Python 3.8+" -ForegroundColor Red
    exit 1
}

$pythonVersion = & $pythonCmd --version 2>&1
Write-Host "Python: $pythonVersion" -ForegroundColor Green

# 检查 Node.js
Write-Host "`n[2/3] 检查 Node.js 环境..." -ForegroundColor Yellow
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Host "错误: 未找到 Node.js，请先安装 Node.js 18+" -ForegroundColor Red
    exit 1
}

$nodeVersion = node --version 2>&1
Write-Host "Node.js: $nodeVersion" -ForegroundColor Green

# 检查依赖
Write-Host "`n[3/3] 检查依赖..." -ForegroundColor Yellow

# 检查 Python 依赖
if (-not (Test-Path "backend\requirements.txt")) {
    Write-Host "警告: 未找到 backend/requirements.txt" -ForegroundColor Yellow
} else {
    Write-Host "后端依赖文件存在" -ForegroundColor Green
}

# 检查 Node 依赖
if (-not (Test-Path "web\node_modules")) {
    Write-Host "警告: 未安装前端依赖，运行: cd web && npm install" -ForegroundColor Yellow
}

# 检查 .env 文件
if (-not (Test-Path ".env")) {
    Write-Host "`n注意: .env 文件不存在，从 .env.example 创建" -ForegroundColor Yellow
    Copy-Item ".env.example" ".env" -ErrorAction SilentlyContinue
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "启动服务..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "后端: http://localhost:8000 (API 文档: /docs)" -ForegroundColor Green
Write-Host "前端: http://localhost:5173" -ForegroundColor Green
Write-Host "`n按 Ctrl+C 停止所有服务`n" -ForegroundColor Gray

# 存储当前目录
$rootDir = Get-Location

# 启动后端
$backendJob = Start-Job -ScriptBlock {
    Set-Location "$using:rootDir\backend"
    python main.py
}

# 启动前端
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:rootDir\web"
    npm run dev
}

# 处理输出
$running = $true
try {
    while ($running) {
        # 检查后端输出
        if ($backendJob.HasMoreData) {
            $output = Receive-Job -Job $backendJob
            foreach ($line in $output) {
                Write-Host "[后端] $line" -ForegroundColor Blue
            }
        }

        # 检查前端输出
        if ($frontendJob.HasMoreData) {
            $output = Receive-Job -Job $frontendJob
            foreach ($line in $output) {
                Write-Host "[前端] $line" -ForegroundColor Magenta
            }
        }

        # 检查作业状态
        if ($backendJob.State -eq "Failed" -or $frontendJob.State -eq "Failed") {
            Write-Host "`n服务启动失败！" -ForegroundColor Red
            $running = $false
        }

        Start-Sleep -Milliseconds 100
    }
} finally {
    # 清理
    Remove-Job -Job $backendJob -Force -ErrorAction SilentlyContinue
    Remove-Job -Job $frontendJob -Force -ErrorAction SilentlyContinue
    Write-Host "`n服务已停止" -ForegroundColor Yellow
}
