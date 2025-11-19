# PowerShell Makefile for Windows
# Usage: .\Makefile.ps1 <command>

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "  RAG System - PowerShell Makefile" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Setup & Installation:" -ForegroundColor Green
    Write-Host "    install           Install production dependencies"
    Write-Host "    dev-install       Install development dependencies"
    Write-Host "    setup-env         Create .env file from template"
    Write-Host "    setup-db          Initialize database"
    Write-Host ""
    Write-Host "  Running Services:" -ForegroundColor Green
    Write-Host "    run-api           Run API server"
    Write-Host "    run-ui            Run Gradio UI"
    Write-Host "    run-all           Run both API and UI"
    Write-Host "    stop-all          Stop all running services"
    Write-Host ""
    Write-Host "  Docker:" -ForegroundColor Green
    Write-Host "    docker-build      Build Docker images"
    Write-Host "    docker-up         Start all Docker services"
    Write-Host "    docker-down       Stop all Docker services"
    Write-Host "    docker-logs       Show Docker logs"
    Write-Host ""
    Write-Host "  Testing:" -ForegroundColor Green
    Write-Host "    test              Run all tests"
    Write-Host "    test-unit         Run unit tests only"
    Write-Host "    test-integration  Run integration tests"
    Write-Host "    coverage          Run tests with coverage"
    Write-Host ""
    Write-Host "  Code Quality:" -ForegroundColor Green
    Write-Host "    lint              Run linters"
    Write-Host "    format            Format code"
    Write-Host "    type-check        Run type checking"
    Write-Host ""
    Write-Host "  Database:" -ForegroundColor Green
    Write-Host "    db-init           Initialize database"
    Write-Host "    db-seed           Seed sample data"
    Write-Host "    db-reset          Reset database (WARNING: deletes all data)"
    Write-Host ""
    Write-Host "  Maintenance:" -ForegroundColor Green
    Write-Host "    clean             Clean generated files"
    Write-Host "    health            Check system health"
    Write-Host "    logs              View application logs"
    Write-Host ""
    Write-Host "Example: .\Makefile.ps1 install" -ForegroundColor Cyan
    Write-Host ""
}

function Install-Dependencies {
    Write-Host "Installing production dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
}

function Install-DevDependencies {
    Write-Host "Installing all dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    pip install -e .
    Write-Host "✓ All dependencies installed" -ForegroundColor Green
}

function Setup-Environment {
    if (Test-Path ".env") {
        Write-Host "✓ .env file already exists" -ForegroundColor Green
    } else {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ .env file created from template" -ForegroundColor Green
        Write-Host "⚠ Please edit .env with your configuration" -ForegroundColor Yellow
    }
}

function Setup-Database {
    Write-Host "Initializing database..." -ForegroundColor Yellow
    python scripts/setup_db.py
}

function Run-API {
    Write-Host "Starting API server..." -ForegroundColor Yellow
    python -m src.api.main
}

function Run-UI {
    Write-Host "Starting Gradio UI..." -ForegroundColor Yellow
    python -m src.ui.gradio_interface
}

function Run-All {
    Write-Host "Starting all services..." -ForegroundColor Yellow
    
    # Start API in background
    $apiJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        python -m src.api.main
    }
    
    Write-Host "API started (Job ID: $($apiJob.Id))" -ForegroundColor Green
    Start-Sleep -Seconds 5
    
    # Start UI in background
    $uiJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        python -m src.ui.gradio_interface
    }
    
    Write-Host "UI started (Job ID: $($uiJob.Id))" -ForegroundColor Green
    
    # Save job IDs
    @{
        api = $apiJob.Id
        ui = $uiJob.Id
    } | ConvertTo-Json | Out-File -FilePath ".jobs.json"
    
    Write-Host ""
    Write-Host "✓ All services started" -ForegroundColor Green
    Write-Host "  API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  UI:  http://localhost:7860" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To stop: .\Makefile.ps1 stop-all" -ForegroundColor Yellow
    
    # Keep showing logs
    Write-Host ""
    Write-Host "Press Ctrl+C to stop watching logs..." -ForegroundColor Yellow
    Get-Job | Receive-Job -Wait
}

function Stop-All {
    Write-Host "Stopping all services..." -ForegroundColor Yellow
    
    if (Test-Path ".jobs.json") {
        $jobs = Get-Content ".jobs.json" | ConvertFrom-Json
        
        Get-Job -Id $jobs.api -ErrorAction SilentlyContinue | Stop-Job
        Get-Job -Id $jobs.api -ErrorAction SilentlyContinue | Remove-Job
        
        Get-Job -Id $jobs.ui -ErrorAction SilentlyContinue | Stop-Job
        Get-Job -Id $jobs.ui -ErrorAction SilentlyContinue | Remove-Job
        
        Remove-Item ".jobs.json"
        
        Write-Host "✓ Services stopped" -ForegroundColor Green
    } else {
        # Stop all Python jobs
        Get-Job | Where-Object { $_.Command -like "*python*" } | Stop-Job
        Get-Job | Where-Object { $_.Command -like "*python*" } | Remove-Job
        
        Write-Host "✓ All jobs stopped" -ForegroundColor Green
    }
}

function Docker-Build {
    Write-Host "Building Docker images..." -ForegroundColor Yellow
    docker-compose -f docker/docker-compose.yml build
    Write-Host "✓ Docker images built" -ForegroundColor Green
}

function Docker-Up {
    Write-Host "Starting Docker services..." -ForegroundColor Yellow
    docker-compose -f docker/docker-compose.yml up -d
    Write-Host "✓ Docker services started" -ForegroundColor Green
    Write-Host ""
    Write-Host "Services running:" -ForegroundColor Cyan
    docker-compose -f docker/docker-compose.yml ps
}

function Docker-Down {
    Write-Host "Stopping Docker services..." -ForegroundColor Yellow
    docker-compose -f docker/docker-compose.yml down
    Write-Host "✓ Docker services stopped" -ForegroundColor Green
}

function Docker-Logs {
    docker-compose -f docker/docker-compose.yml logs -f
}

function Run-Tests {
    Write-Host "Running all tests..." -ForegroundColor Yellow
    pytest tests/ -v
}

function Run-UnitTests {
    Write-Host "Running unit tests..." -ForegroundColor Yellow
    pytest tests/ -v -m "not integration"
}

function Run-IntegrationTests {
    Write-Host "Running integration tests..." -ForegroundColor Yellow
    pytest tests/ -v -m integration
}

function Run-Coverage {
    Write-Host "Running tests with coverage..." -ForegroundColor Yellow
    pytest tests/ -v --cov=src --cov-report=html --cov-report=term
    Write-Host ""
    Write-Host "✓ Coverage report generated in htmlcov/" -ForegroundColor Green
}

function Run-Lint {
    Write-Host "Running linters..." -ForegroundColor Yellow
    
    Write-Host "  → flake8..." -ForegroundColor Cyan
    flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
    flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    Write-Host "✓ Linting complete" -ForegroundColor Green
}

function Format-Code {
    Write-Host "Formatting code..." -ForegroundColor Yellow
    
    Write-Host "  → black..." -ForegroundColor Cyan
    black src/ tests/
    
    Write-Host "  → isort..." -ForegroundColor Cyan
    isort src/ tests/
    
    Write-Host "✓ Code formatted" -ForegroundColor Green
}

function Type-Check {
    Write-Host "Running type checker..." -ForegroundColor Yellow
    mypy src/ --ignore-missing-imports
    Write-Host "✓ Type checking complete" -ForegroundColor Green
}

function Initialize-Database {
    Write-Host "Initializing database..." -ForegroundColor Yellow
    python scripts/setup_db.py
}

function Seed-Database {
    Write-Host "Seeding database..." -ForegroundColor Yellow
    python scripts/seed_data.py
}

function Reset-Database {
    Write-Host "⚠ WARNING: This will delete all data!" -ForegroundColor Red
    $response = Read-Host "Are you sure? (yes/no)"
    
    if ($response -eq "yes") {
        python scripts/setup_db.py --recreate
        Write-Host "✓ Database reset" -ForegroundColor Green
    } else {
        Write-Host "✗ Aborted" -ForegroundColor Yellow
    }
}

function Clean-Files {
    Write-Host "Cleaning generated files..." -ForegroundColor Yellow
    
    # Python cache
    Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Force -Recurse
    Get-ChildItem -Path . -Include *.pyc -Recurse -Force | Remove-Item -Force
    Get-ChildItem -Path . -Include *.pyo -Recurse -Force | Remove-Item -Force
    
    # Build artifacts
    if (Test-Path "build") { Remove-Item -Path "build" -Recurse -Force }
    if (Test-Path "dist") { Remove-Item -Path "dist" -Recurse -Force }
    if (Test-Path "*.egg-info") { Remove-Item -Path "*.egg-info" -Recurse -Force }
    
    # Test artifacts
    if (Test-Path ".pytest_cache") { Remove-Item -Path ".pytest_cache" -Recurse -Force }
    if (Test-Path "htmlcov") { Remove-Item -Path "htmlcov" -Recurse -Force }
    if (Test-Path ".coverage") { Remove-Item -Path ".coverage" -Force }
    
    Write-Host "✓ Cleanup complete" -ForegroundColor Green
}

function Check-Health {
    Write-Host "Checking system health..." -ForegroundColor Yellow
    python scripts/health_check.py
}

function Show-Logs {
    if (Test-Path "logs") {
        Get-Content "logs/app_*.log" -Tail 50 -Wait
    } else {
        Write-Host "✗ No logs found" -ForegroundColor Red
    }
}

# Command routing
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "install" { Install-Dependencies }
    "dev-install" { Install-DevDependencies }
    "setup-env" { Setup-Environment }
    "setup-db" { Setup-Database }
    "run-api" { Run-API }
    "run-ui" { Run-UI }
    "run-all" { Run-All }
    "stop-all" { Stop-All }
    "docker-build" { Docker-Build }
    "docker-up" { Docker-Up }
    "docker-down" { Docker-Down }
    "docker-logs" { Docker-Logs }
    "test" { Run-Tests }
    "test-unit" { Run-UnitTests }
    "test-integration" { Run-IntegrationTests }
    "coverage" { Run-Coverage }
    "lint" { Run-Lint }
    "format" { Format-Code }
    "type-check" { Type-Check }
    "db-init" { Initialize-Database }
    "db-seed" { Seed-Database }
    "db-reset" { Reset-Database }
    "clean" { Clean-Files }
    "health" { Check-Health }
    "logs" { Show-Logs }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
        exit 1
    }
}