# Deployment Helper Script
# Save as: deploy.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [string]$Username = "root"
)

Write-Host "`n🚀 Deploying to: $ServerIP" -ForegroundColor Cyan

# 1. Upload files
Write-Host "`n[1/5] Uploading files..." -ForegroundColor Yellow
scp -r src docker airflow requirements.txt .env $Username@${ServerIP}:/root/app/

# 2. Install Docker
Write-Host "`n[2/5] Installing Docker..." -ForegroundColor Yellow
ssh $Username@$ServerIP "curl -fsSL https://get.docker.com | sh && apt install docker-compose -y"

# 3. Start services
Write-Host "`n[3/5] Starting services..." -ForegroundColor Yellow
ssh $Username@$ServerIP "cd /root/app/docker && docker-compose up -d"

# 4. Wait for startup
Write-Host "`n[4/5] Waiting for services..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# 5. Check status
Write-Host "`n[5/5] Checking status..." -ForegroundColor Yellow
ssh $Username@$ServerIP "cd /root/app/docker && docker-compose ps"

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
Write-Host "Access at: http://${ServerIP}:7860" -ForegroundColor Cyan

# Usage:
# .\deploy.ps1 -ServerIP "123.45.67.89"
