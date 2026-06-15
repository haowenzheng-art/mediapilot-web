# MediaPilot API Test Script (with Auth)
# Usage: .\test_api_with_auth.ps1
# First run: python -m backend.scripts.create_test_user
$ErrorActionPreference = "Stop"
$BASE_URL = "http://localhost:8000/api/v1"
$TOKEN_FILE = Join-Path $PSScriptRoot "test_token.txt"

# -- Helper --
function Write-Result {
    param(
        [string]$Name,
        [bool]$Ok,
        [string]$Detail = ""
    )
    if ($Ok) {
        Write-Host "  [PASS] " -ForegroundColor Green -NoNewline
        Write-Host "$Name" -NoNewline
        if ($Detail) { Write-Host " - $Detail" } else { Write-Host "" }
    } else {
        Write-Host "  [FAIL] " -ForegroundColor Red -NoNewline
        Write-Host "$Name" -NoNewline
        if ($Detail) { Write-Host " - $Detail" } else { Write-Host "" }
    }
}

# -- Counters --
$script:passed = 0
$script:failed = 0
$script:TOKEN = $null

# -- Start --
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  MediaPilot API Test (with Auth)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# Section 1: No auth required
# ============================================================
Write-Host "--- No auth required ---" -ForegroundColor Yellow
Write-Host ""

# Test 1: Health Check
Write-Host "1. Health Check" -ForegroundColor Cyan
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    $data = $resp.Content | ConvertFrom-Json
    $ai = $data.services.ai_service
    $engine = $data.services.transcribe_engine
    Write-Result -Name "Health Check" -Ok ($resp.StatusCode -eq 200) -Detail "AI=$ai, engine=$engine"
    $script:passed++
} catch {
    Write-Result -Name "Health Check" -Ok $false -Detail $_.Exception.Message
    $script:failed++
}

# Test 2: Read token
Write-Host "2. Read Token" -ForegroundColor Cyan
if (Test-Path $TOKEN_FILE) {
    $script:TOKEN = (Get-Content $TOKEN_FILE -Raw).Trim()
    $tokenPreview = ""
    if ($script:TOKEN.Length -gt 20) {
        $tokenPreview = $script:TOKEN.Substring(0, 20) + "..."
    } else {
        $tokenPreview = $script:TOKEN
    }
    Write-Result -Name "Token Read" -Ok ($script:TOKEN.Length -gt 10) -Detail $tokenPreview
    $script:passed++
} else {
    Write-Result -Name "Token Read" -Ok $false -Detail "File not found: $TOKEN_FILE"
    Write-Host "         Run first: python -m backend.scripts.create_test_user" -ForegroundColor DarkGray
    $script:failed++
}

Write-Host ""

# ============================================================
# Section 2: Auth required
# ============================================================
Write-Host "--- Auth required ---" -ForegroundColor Yellow
Write-Host ""

if (-not $script:TOKEN) {
    Write-Host "  Skipped (no token). Run:" -ForegroundColor Red
    Write-Host "  python -m backend.scripts.create_test_user" -ForegroundColor Red
    Write-Host ""
} else {
    $authHeaders = @{
        "Content-Type"  = "application/json"
        "Authorization" = "Bearer $script:TOKEN"
    }

    # Test 3: Trending Search
    Write-Host "3. Trending Search" -ForegroundColor Cyan
    try {
        $body = @{keyword = "AI"; platforms = @("douyin", "xiaohongshu"); days = 7} | ConvertTo-Json
        $resp = Invoke-WebRequest -Uri "$BASE_URL/trending/search" -Method POST -Body $body -Headers $authHeaders -UseBasicParsing -TimeoutSec 10
        $data = $resp.Content | ConvertFrom-Json
        $count = $data.data.hot_topics.Count
        Write-Result -Name "Trending Search" -Ok ($resp.StatusCode -eq 200 -and $data.success) -Detail "$count topics"
        $script:passed++
    } catch {
        $errMsg = $_.Exception.Message
        if ($errMsg -match "401") { $errMsg = "$errMsg - Token invalid, rerun create_test_user" }
        Write-Result -Name "Trending Search" -Ok $false -Detail $errMsg
        $script:failed++
    }

    # Test 4: Competitor Search
    Write-Host "4. Competitor Search" -ForegroundColor Cyan
    try {
        $body = @{niche = "beauty"; platforms = @("douyin", "xiaohongshu"); min_followers = 10000; max_followers = 1000000} | ConvertTo-Json
        $resp = Invoke-WebRequest -Uri "$BASE_URL/competitors/search" -Method POST -Body $body -Headers $authHeaders -UseBasicParsing -TimeoutSec 10
        $data = $resp.Content | ConvertFrom-Json
        $count = $data.data.competitors.Count
        Write-Result -Name "Competitor Search" -Ok ($resp.StatusCode -eq 200 -and $data.success) -Detail "$count accounts"
        $script:passed++
    } catch {
        $errMsg = $_.Exception.Message
        if ($errMsg -match "401") { $errMsg = "$errMsg - Token invalid, rerun create_test_user" }
        Write-Result -Name "Competitor Search" -Ok $false -Detail $errMsg
        $script:failed++
    }

    Write-Host ""
}

# ============================================================
# Section 3: No auth required APIs
# ============================================================
Write-Host "--- No auth required APIs ---" -ForegroundColor Yellow
Write-Host ""

# Test 5: Content Generate
Write-Host "5. Content Generate" -ForegroundColor Cyan
try {
    $body = @{topic = "productivity"; platform = "douyin"; duration = 60; style = "professional"} | ConvertTo-Json
    $resp = Invoke-WebRequest -Uri "$BASE_URL/content/generate" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 30
    $data = $resp.Content | ConvertFrom-Json
    $shotCount = $data.data.script.Count
    $title = $data.data.copywriting.title
    Write-Result -Name "Content Generate" -Ok ($resp.StatusCode -eq 200) -Detail "$shotCount shots, title: $title"
    $script:passed++
} catch {
    Write-Result -Name "Content Generate" -Ok $false -Detail $_.Exception.Message
    $script:failed++
}

# Test 6: Video Fetch
Write-Host "6. Video Fetch" -ForegroundColor Cyan
try {
    $body = @{video_url = "https://www.douyin.com/video/123456"; platform = "douyin"} | ConvertTo-Json
    $resp = Invoke-WebRequest -Uri "$BASE_URL/video/fetch" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 10
    $data = $resp.Content | ConvertFrom-Json
    Write-Result -Name "Video Fetch" -Ok ($resp.StatusCode -eq 200) -Detail "url=$($data.data.url), views=$($data.data.view_count)"
    $script:passed++
} catch {
    Write-Result -Name "Video Fetch" -Ok $false -Detail $_.Exception.Message
    $script:failed++
}

# Test 7: Video Transcript
Write-Host "7. Video Transcript" -ForegroundColor Cyan
try {
    $body = @{video_id = "123456"} | ConvertTo-Json
    $resp = Invoke-WebRequest -Uri "$BASE_URL/video/transcript" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 10
    $data = $resp.Content | ConvertFrom-Json
    $lineCount = $data.data.lines.Count
    Write-Result -Name "Video Transcript" -Ok ($resp.StatusCode -eq 200) -Detail "$lineCount lines"
    $script:passed++
} catch {
    Write-Result -Name "Video Transcript" -Ok $false -Detail $_.Exception.Message
    $script:failed++
}

# Test 8: Video Rewrite
Write-Host "8. Video Rewrite" -ForegroundColor Cyan
try {
    $body = @{transcript = "sharing productivity tips today"; style = "professional"; target_duration = 60} | ConvertTo-Json
    $resp = Invoke-WebRequest -Uri "$BASE_URL/video/rewrite" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 30
    $data = $resp.Content | ConvertFrom-Json
    if ($data.success -and $data.data.rewritten_text) {
        $preview = $data.data.rewritten_text
        if ($preview.Length -gt 60) { $preview = $preview.Substring(0, 60) + "..." }
        Write-Result -Name "Video Rewrite" -Ok $true -Detail $preview
        $script:passed++
    } else {
        Write-Result -Name "Video Rewrite" -Ok $false -Detail $data.message
        $script:failed++
    }
} catch {
    Write-Result -Name "Video Rewrite" -Ok $false -Detail $_.Exception.Message
    $script:failed++
}

# -- Summary --
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
$total = $script:passed + $script:failed
if ($script:failed -eq 0) {
    Write-Host "  Result: $script:passed/$total all passed" -ForegroundColor Green
} else {
    Write-Host "  Result: $script:passed/$total passed, $script:failed failed" -ForegroundColor Red
}
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
