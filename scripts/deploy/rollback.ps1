# =============================================================================
# ROLLBACK SCRIPT - WINDOWS
# =============================================================================

$ErrorActionPreference = "Stop"

param(
    [string]$Environment = "production"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "ROLLBACK TO PREVIOUS VERSION" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$DOCKER_COMPOSE_FILE = "docker/docker-compose.yml"

Write-Host "`n⚠️  WARNING: Rolling back to previous version!" -ForegroundColor Yellow
$confirmation = Read-Host "Confirm rollback? Type 'ROLLBACK' to continue"

if ($confirmation -ne "ROLLBACK") {
    Write-Host "❌ Rollback cancelled" -ForegroundColor Red
    exit 1
}

# Stop current containers
Write-Host "`n🛑 Stopping current containers..." -ForegroundColor Green
docker-compose -f $DOCKER_COMPOSE_FILE down

# Checkout previous commit
Write-Host "`n⏮️  Reverting to previous version..." -ForegroundColor Green
git checkout HEAD~1

# Rebuild and restart
Write-Host "`n🏗️  Rebuilding..." -ForegroundColor Green
docker-compose -f $DOCKER_COMPOSE_FILE build

Write-Host "`n🚀 Starting services..." -ForegroundColor Green
docker-compose -f $DOCKER_COMPOSE_FILE up -d

# Health check
Start-Sleep -Seconds 10

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "`n✅ Rollback successful!" -ForegroundColor Green
    }
}
catch {
    Write-Host "❌ Rollback failed! Check logs." -ForegroundColor Red
    docker-compose -f $DOCKER_COMPOSE_FILE logs
    exit 1
}

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "✅ ROLLBACK COMPLETE" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green