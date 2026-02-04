$baseUrl = "http://127.0.0.1:8000/process"

function Test-Tool {
    param(
        [string]$ToolName,
        [string]$Task
    )
    Write-Host "Testing $ToolName..." -NoNewline
    $body = @{task = $Task} | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri $baseUrl -Method Post -Body $body -ContentType "application/json"
        if ($response.success -eq $true) {
            Write-Host " [OK] ✅" -ForegroundColor Green
            # Write-Host "Summary: $($response.response.summary)" -ForegroundColor Gray
        } else {
            Write-Host " [FAILED] ❌" -ForegroundColor Red
            Write-Host "Error: $($response.error)" -ForegroundColor Red
        }
    } catch {
        Write-Host " [FAILED] ❌ (Request Error)" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

Write-Host "Starting Comprehensive Tool Test..." -ForegroundColor Cyan
Write-Host "-----------------------------------"

Test-Tool "GitHub" "Find top 1 trending Python repository on GitHub"
Test-Tool "Weather" "What is the current weather in Tokyo?"
Test-Tool "News" "Get the latest top headline technology news in the US"
Test-Tool "Wikipedia" "Search Wikipedia for 'Artificial Intelligence'"
Test-Tool "Jokes" "Tell me a programming joke"
Test-Tool "Quotes" "Give me an inspirational quote"

Write-Host "-----------------------------------"
Write-Host "Test Complete!" -ForegroundColor Cyan
