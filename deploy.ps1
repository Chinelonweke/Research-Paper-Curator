# Save as: deploy.ps1
# Run with: .\deploy.ps1

Write-Host "`nRESTARTING DOCKER..." -ForegroundColor Cyan

# Stop
docker-compose -f docker/docker-compose.yml down

# Start database
docker-compose -f docker/docker-compose.yml up -d postgres redis
Write-Host "Waiting 30s for database..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Start API and UI  
docker-compose -f docker/docker-compose.yml up -d api ui
Write-Host "Waiting 30s for API..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Test
Write-Host "`nContainer Status:" -ForegroundColor Cyan
docker-compose -f docker/docker-compose.yml ps

Write-Host "`nTesting API..." -ForegroundColor Cyan
curl http://localhost:8000/health

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "DONE! Open these:" -ForegroundColor Green
Write-Host "UI:   http://localhost:7860" -ForegroundColor Cyan
Write-Host "API:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Green