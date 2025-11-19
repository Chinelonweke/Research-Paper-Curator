# =============================================================================
# BUILD AND START SCRIPT
# =============================================================================

cd C:\Users\chinelo\Research-Paper-Curator

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "BUILDING AND STARTING" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "✗ .env file not found!" -ForegroundColor Red
    Write-Host "Create .env file with your GROQ_API_KEY before building" -ForegroundColor Yellow
    exit
}

Write-Host "`nBuilding all services..." -ForegroundColor Yellow
Write-Host "This will take 10-15 minutes" -ForegroundColor Cyan

docker-compose -f docker/docker-compose.yml build

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n✗ BUILD FAILED!" -ForegroundColor Red
    Write-Host "Check errors above" -ForegroundColor Yellow
    exit
}

Write-Host "`n✓ BUILD SUCCESSFUL!" -ForegroundColor Green

Write-Host "`nStarting all services..." -ForegroundColor Yellow
docker-compose -f docker/docker-compose.yml up -d

Write-Host "`nWaiting 90 seconds for services to initialize..." -ForegroundColor Cyan
for ($i = 90; $i -gt 0; $i -= 10) {
    Write-Host "  $i seconds..." -ForegroundColor Gray
    Start-Sleep -Seconds 10
}

Write-Host "`nChecking status..." -ForegroundColor Yellow
docker-compose -f docker/docker-compose.yml ps

Write-Host "`nTesting API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 10
    Write-Host "✓ API is working!" -ForegroundColor Green
    Write-Host $response.Content -ForegroundColor Cyan
}
catch {
    Write-Host "⚠️  API not responding yet" -ForegroundColor Yellow
    docker-compose -f docker/docker-compose.yml logs api --tail=15
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "🎉 COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host "`nAccess your application:" -ForegroundColor Yellow
Write-Host "  • UI:          http://localhost:7860" -ForegroundColor Cyan
Write-Host "  • API:         http://localhost:8000" -ForegroundColor Cyan
Write-Host "  • API Docs:    http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  • OpenSearch:  http://localhost:9200" -ForegroundColor Cyan
Write-Host "  • Airflow:     http://localhost:8080 (admin/admin)" -ForegroundColor Cyan

Start-Process "http://localhost:7860"
Start-Process "http://localhost:8000/docs"

Write-Host "`nDone!" -ForegroundColor Green
