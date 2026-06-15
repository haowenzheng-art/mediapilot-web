# MediaPilot API Test Script
$ErrorActionPreference = "Stop"
$BASE_URL = "http://localhost:8000/api/v1"

Write-Host "`n============================================================"
Write-Host "  MediaPilot 后端功能测试"
Write-Host "============================================================`n"

# Test 1: Health Check
Write-Host "1. 健康检查`n" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($data | ConvertTo-Json -Depth 3)`n"
} catch {
    Write-Host "ERROR: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 2: Trending Search
Write-Host "2. 热点搜索`n" -ForegroundColor Cyan
try {
    $body = @{
        keyword = "AI"
        platforms = @("douyin", "xiaohongshu")
        days = 7
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "$BASE_URL/trending/search" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green

    if ($response.StatusCode -eq 200) {
        $total = $data.data.total_count
        $topics = $data.data.hot_topics
        Write-Host "Found $total hot topics"
        if ($topics.Count -gt 0) {
            Write-Host "First topic: $($topics[0] | ConvertTo-Json -Depth 3)"
        }
    }
    Write-Host ""
} catch {
    Write-Host "ERROR: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 3: Competitor Search
Write-Host "3. 对标账号搜索`n" -ForegroundColor Cyan
try {
    $body = @{
        niche = "beauty"
        platforms = @("douyin", "xiaohongshu")
        min_followers = 10000
        max_followers = 1000000
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "$BASE_URL/competitors/search" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green

    if ($response.StatusCode -eq 200) {
        $total = $data.data.total_count
        $accounts = $data.data.accounts
        Write-Host "Found $total competitor accounts"
        if ($accounts.Count -gt 0) {
            Write-Host "First account: $($accounts[0] | ConvertTo-Json -Depth 3)"
        }
    }
    Write-Host ""
} catch {
    Write-Host "ERROR: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 4: Content Generate
Write-Host "4. 脚本生成`n" -ForegroundColor Cyan
try {
    $body = @{
        topic = "How to improve work efficiency"
        platform = "douyin"
        duration = 60
        style = "professional"
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "$BASE_URL/content/generate" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 30
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green

    if ($response.StatusCode -eq 200) {
        $script = $data.data.script
        $copywriting = $data.data.copywriting
        Write-Host "Generated $($script.Count) shots"
        Write-Host "Title: $($copywriting.title)"
        Write-Host "Hooks: $($copywriting.hooks -join ', ')"
        if ($script.Count -gt 0) {
            Write-Host "First shot: $($script[0] | ConvertTo-Json -Depth 2)"
        }
    }
    Write-Host ""
} catch {
    Write-Host "ERROR: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 5: Video Fetch
Write-Host "5. 视频信息获取`n" -ForegroundColor Cyan
try {
    $body = @{
        video_url = "https://www.douyin.com/video/123456"
        platform = "douyin"
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "$BASE_URL/video/fetch" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Video Info: $($data.data | ConvertTo-Json -Depth 2)`n"
} catch {
    Write-Host "ERROR: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 6: Video Transcript
Write-Host "6. 视频逐字稿获取`n" -ForegroundColor Cyan
try {
    $body = @{
        video_id = "123456"
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "$BASE_URL/video/transcript" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green

    if ($response.StatusCode -eq 200) {
        $fullText = $data.data.full_transcript
        $lines = $data.data.lines
        Write-Host "Full transcript length: $($fullText.Length) characters"
        Write-Host "Lines count: $($lines.Count)"
        if ($lines.Count -gt 0) {
            Write-Host "First line: $($lines[0] | ConvertTo-Json -Depth 2)"
        }
    }
    Write-Host ""
} catch {
    Write-Host "ERROR: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 7: Video Rewrite
Write-Host "7. 文案改写`n" -ForegroundColor Cyan
try {
    $body = @{
        transcript = "Today we will talk about work efficiency topics, hope to help everyone."
        style = "professional"
        target_duration = 60
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "$BASE_URL/video/rewrite" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 30
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green

    if ($response.StatusCode -eq 200) {
        $rewritten = $data.data.rewritten_text
        $shortened = if ($rewritten.Length -gt 200) { $rewritten.Substring(0, 200) + "..." } else { $rewritten }
        Write-Host "Rewritten: $shortened"
    }
    Write-Host ""
} catch {
    Write-Host "ERROR: $($_.Exception.Message)`n" -ForegroundColor Red
}

Write-Host "============================================================"
Write-Host "  测试完成"
Write-Host "============================================================`n"