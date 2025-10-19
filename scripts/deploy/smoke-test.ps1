# =============================================================================
# SMOKE TESTS - WINDOWS
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "RUNNING SMOKE TESTS" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$API_URL = if ($env:API_URL) { $env:API_URL } else { "http://localhost:8000" }
$PASSED = 0
$FAILED = 0

# Test function
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200
    )
    
    Write-Host -NoNewline "Testing $Name... "
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        $status = $response.StatusCode
        
        if ($status -eq $ExpectedStatus) {
            Write-Host "✅ PASSED (HTTP $status)" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ FAILED (Expected $ExpectedStatus, got $status)" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ FAILED ($($_.Exception.Message))" -ForegroundColor Red
        return $false
    }
}

# Run tests
Write-Host "`n"
if (Test-Endpoint "Root endpoint" "$API_URL/") { $PASSED++ } else { $FAILED++ }
if (Test-Endpoint "Health check" "$API_URL/health") { $PASSED++ } else { $FAILED++ }
if (Test-Endpoint "Detailed health" "$API_URL/health/detailed") { $PASSED++ } else { $FAILED++ }
if (Test-Endpoint "API papers list" "$API_URL/api/papers") { $PASSED++ } else { $FAILED++ }
if (Test-Endpoint "API stats" "$API_URL/api/stats") { $PASSED++ } else { $FAILED++ }

# Search test
Write-Host -NoNewline "Testing search endpoint... "
try {
    $body = @{
        query = "machine learning"
        top_k = 5
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$API_URL/api/search" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10
    
    if ($response.query) {
        Write-Host "✅ PASSED" -ForegroundColor Green
        $PASSED++
    }
    else {
        Write-Host "❌ FAILED" -ForegroundColor Red
        $FAILED++
    }
}
catch {
    Write-Host "❌ FAILED" -ForegroundColor Red
    $FAILED++
}

# Summary
Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "SMOKE TEST SUMMARY" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Passed: " -NoNewline
Write-Host "$PASSED" -ForegroundColor Green
Write-Host "Failed: " -NoNewline
Write-Host "$FAILED" -ForegroundColor Red
Write-Host "==========================================" -ForegroundColor Cyan

if ($FAILED -gt 0) {
    Write-Host "`n❌ Some tests failed!" -ForegroundColor Red
    exit 1
}
else {
    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
    exit 0
}