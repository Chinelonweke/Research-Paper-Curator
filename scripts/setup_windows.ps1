# Windows Setup Script for RAG System
# Run this with: powershell -ExecutionPolicy Bypass -File setup_windows.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  RAG System - Windows Setup Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.9 or higher." -ForegroundColor Red
    exit 1
}

# Check Python version
$version = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$version -lt [version]"3.9") {
    Write-Host "✗ Python version must be 3.9 or higher. Current: $version" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host "✓ pip upgraded" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Install development dependencies
Write-Host ""
Write-Host "Installing development dependencies..." -ForegroundColor Yellow
pip install -r requirements-dev.txt
Write-Host "✓ Development dependencies installed" -ForegroundColor Green

# Install package in editable mode
Write-Host ""
Write-Host "Installing package in editable mode..." -ForegroundColor Yellow
pip install -e .
Write-Host "✓ Package installed" -ForegroundColor Green

# Create .env file
Write-Host ""
Write-Host "Setting up environment variables..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env file created from template" -ForegroundColor Green
    Write-Host "⚠ Please edit .env file with your configuration" -ForegroundColor Yellow
}

# Create directories
Write-Host ""
Write-Host "Creating necessary directories..." -ForegroundColor Yellow
$directories = @("logs", "data", "models")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "✓ Created directory: $dir" -ForegroundColor Green
    }
}

# Check for Docker
Write-Host ""
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "✓ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found. Install Docker Desktop for Windows to use containerized services." -ForegroundColor Yellow
}

# Check for Docker Compose
Write-Host ""
Write-Host "Checking Docker Compose installation..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version 2>&1
    Write-Host "✓ Docker Compose found: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose not found." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your configuration" -ForegroundColor White
Write-Host "2. Install and start services:" -ForegroundColor White
Write-Host "   - PostgreSQL (download from https://www.postgresql.org/download/windows/)" -ForegroundColor White
Write-Host "   - Redis (download from https://github.com/microsoftarchive/redis/releases)" -ForegroundColor White
Write-Host "   - Ollama (download from https://ollama.ai)" -ForegroundColor White
Write-Host "   OR use Docker: docker-compose -f docker/docker-compose.yml up -d" -ForegroundColor White
Write-Host "3. Initialize database: python scripts/setup_db.py" -ForegroundColor White
Write-Host "4. Run the API: python -m src.api.main" -ForegroundColor White
Write-Host "5. Run the UI: python -m src.ui.gradio_interface" -ForegroundColor White
Write-Host ""
Write-Host "For detailed instructions, see docs/WINDOWS_SETUP.md" -ForegroundColor Cyan