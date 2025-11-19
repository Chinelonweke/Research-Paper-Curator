# =============================================================================
# PRODUCTION DEPLOYMENT SCRIPT - WINDOWS
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "PRODUCTION DEPLOYMENT" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Configuration
$ENVIRONMENT = "production"
$DOCKER_COMPOSE_FILE = "docker/docker-compose.yml"
$ENV_FILE = "environments/.env.production"

# Safety check
Write-Host "`n⚠️  WARNING: You are about to deploy to PRODUCTION!" -ForegroundColor Yellow
$confirmation = Read-Host "Are you sure? Type 'DEPLOY' to confirm"

if ($confirmation -ne "DEPLOY") {
    Write-Host "❌ Deployment cancelled" -ForegroundColor Red
    exit 1
}

# Check if env file exists
if (-Not (Test-Path $ENV_FILE)) {
    Write-Host "❌ Environment file not found: $ENV_FILE" -ForegroundColor Red
    exit 1
}

# Pull latest code
Write-Host "`n📥 Pulling latest code..." -ForegroundColor Green
git pull origin main

# Build images
Write-Host "`n🏗️  Building Docker images..." -ForegroundColor Green
docker-compose -f $DOCKER_COMPOSE_FILE build --no-cache

# Stop old containers
Write-Host "`n🛑 Stopping old containers..." -ForegroundColor Green
docker-compose -f $DOCKER_COMPOSE_FILE down

# Start new containers
Write-Host "`n🚀 Starting new containers..." -ForegroundColor Green
docker-compose -f $DOCKER_COMPOSE_FILE --env-file $ENV_FILE up -d

# Wait for services
Write-Host "`n⏳ Waiting for services to be healthy..." -ForegroundColor Green
Start-Sleep -Seconds 10

# Health check
Write-Host "`n🏥 Running health checks..." -ForegroundColor Green
$MAX_RETRIES = 30
$RETRY_COUNT = 0
$HEALTH_OK = $false

while ($RETRY_COUNT -lt $MAX_RETRIES) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Health check passed!" -ForegroundColor Green
            $HEALTH_OK = $true
            break
        }
    }
    catch {
        $RETRY_COUNT++
        Write-Host "Attempt $RETRY_COUNT/$MAX_RETRIES..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

if (-Not $HEALTH_OK) {
    Write-Host "❌ Health check failed!" -ForegroundColor Red
    Write-Host "Rolling back..." -ForegroundColor Red
    docker-compose -f $DOCKER_COMPOSE_FILE down
    exit 1
}

# Run migrations
Write-Host "`n📊 Running database migrations..." -ForegroundColor Green
docker-compose -f $DOCKER_COMPOSE_FILE exec -T api python scripts/migrate_add_embeddings.py

# Show status
Write-Host "`n📊 Container status:" -ForegroundColor Green
docker-compose -f $DOCKER_COMPOSE_FILE ps

# Show logs
Write-Host "`n📋 Recent logs:" -ForegroundColor Green
docker-compose -f $DOCKER_COMPOSE_FILE logs --tail=50

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "✅ DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "UI: http://localhost:7860" -ForegroundColor Cyan
Write-Host "Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Green