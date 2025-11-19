# =============================================================================
# SETUP SCRIPT - Create directories and backup files
# =============================================================================

cd C:\Users\chinelo\Research-Paper-Curator

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SETUP: Creating directories" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Create directories
$dirs = @("docker", "airflow/dags", "airflow/logs", "airflow/plugins", "logs", "data")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "✓ Created $dir" -ForegroundColor Green
    } else {
        Write-Host "✓ $dir already exists" -ForegroundColor Cyan
    }
}

# Backup existing files
Write-Host "`nBacking up existing files..." -ForegroundColor Yellow

if (Test-Path docker/Dockerfile) {
    Copy-Item docker/Dockerfile docker/Dockerfile.backup -Force
    Write-Host "✓ Backed up docker/Dockerfile" -ForegroundColor Green
}

if (Test-Path requirements.txt) {
    Copy-Item requirements.txt requirements.txt.backup -Force
    Write-Host "✓ Backed up requirements.txt" -ForegroundColor Green
}

if (Test-Path docker/docker-compose.yml) {
    Copy-Item docker/docker-compose.yml docker/docker-compose.yml.backup -Force
    Write-Host "✓ Backed up docker-compose.yml" -ForegroundColor Green
}

# Copy .env if exists
if (Test-Path .env) {
    Copy-Item .env docker/.env -Force
    Write-Host "✓ Copied .env to docker/.env" -ForegroundColor Green
} else {
    Write-Host "⚠️  .env not found - create it before building!" -ForegroundColor Yellow
}

Write-Host "`n✓ Setup complete!" -ForegroundColor Green
Write-Host "Now copy the individual files to their locations" -ForegroundColor Cyan
