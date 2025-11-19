# Windows Setup Guide

Complete guide for setting up the RAG system on Windows.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
- [Service Setup](#service-setup)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

1. **Python 3.9 or higher**
   - Download from: https://www.python.org/downloads/
   - ⚠️ Make sure to check "Add Python to PATH" during installation

2. **Git**
   - Download from: https://git-scm.com/download/win
   - Use default settings during installation

3. **Visual Studio Build Tools** (for some Python packages)
   - Download from: https://visualstudio.microsoft.com/downloads/
   - Select "Desktop development with C++" workload

### Optional (Recommended)

4. **Windows Terminal**
   - Install from Microsoft Store
   - Better terminal experience than CMD

5. **Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop
   - Easier service management

## Installation Steps

### Step 1: Clone Repository
```powershell
# Open PowerShell or Windows Terminal
cd C:\Projects  # or your preferred location
git clone https://github.com/yourusername/research-paper-curator.git
cd research-paper-curator
```

### Step 2: Run Setup Script
```powershell
# Allow script execution (run PowerShell as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run setup
.\scripts\setup_windows.ps1
```

This script will:
- ✓ Check Python installation
- ✓ Create virtual environment
- ✓ Install dependencies
- ✓ Create `.env` file
- ✓ Create necessary directories

### Step 3: Configure Environment

Edit `.env` file with your settings:
```bash
# Open in notepad
notepad .env

# Or use VS Code
code .env
```

## Service Setup

### Option 1: Docker (Recommended)

**Install Docker Desktop:**
1. Download from https://www.docker.com/products/docker-desktop
2. Install and restart computer
3. Start Docker Desktop
4. Wait for Docker to be ready (whale icon in system tray)

**Start Services:**
```powershell
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Check status
docker-compose -f docker/docker-compose.yml ps

# View logs
docker-compose -f docker/docker-compose.yml logs -f api
```

### Option 2: Manual Installation

#### PostgreSQL

1. **Download and Install:**
   - Go to: https://www.postgresql.org/download/windows/
   - Download PostgreSQL 15 installer
   - Run installer with default settings
   - Remember the password you set for postgres user

2. **Create Database:**
```powershell
# Open psql (PostgreSQL command line)
# Find it in Start Menu → PostgreSQL → psql

# In psql:
CREATE DATABASE research_papers;
\q
```

3. **Update .env:**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=research_papers
DB_USER=postgres
DB_PASSWORD=your_password_here
```

#### Redis

1. **Download:**
   - Go to: https://github.com/microsoftarchive/redis/releases
   - Download latest `.msi` file (e.g., Redis-x64-5.0.14.msi)

2. **Install:**
   - Run the installer
   - Use default settings
   - Redis will start automatically as a Windows service

3. **Verify:**
```powershell
# In PowerShell
redis-cli ping
# Should return: PONG
```

#### OpenSearch

**Using Docker (Easiest):**
```powershell
docker run -d --name opensearch \
  -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m" \
  -e "DISABLE_SECURITY_PLUGIN=true" \
  opensearchproject/opensearch:2.11.0
```

**Verify:**
```powershell
# Test connection
curl http://localhost:9200

# Or in browser
# Navigate to: http://localhost:9200
```

#### Ollama (LLM)

1. **Download and Install:**
   - Go to: https://ollama.ai
   - Download Windows installer
   - Run installer

2. **Pull Model:**
```powershell
# Open Command Prompt or PowerShell
ollama pull llama2

# Verify
ollama list
```

3. **Test:**
```powershell
ollama run llama2 "Hello!"
```

## Initialize System

### Step 1: Activate Virtual Environment
```powershell
# In project directory
.\venv\Scripts\Activate.ps1

# You should see (venv) in your prompt
```

### Step 2: Initialize Database
```powershell
python scripts\setup_db.py
```

### Step 3: Seed Sample Data
```powershell
python scripts\seed_data.py
```

This will fetch and process 10 recent papers from arXiv.

### Step 4: Test Components
```powershell
python scripts\test_components.py
```

All components should show as healthy.

## Running the System

### Method 1: Using PowerShell Makefile
```powershell
# Start both API and UI
.\Makefile.ps1 run-all

# Or start separately:
# Terminal 1
.\Makefile.ps1 run-api

# Terminal 2
.\Makefile.ps1 run-ui
```

### Method 2: Manual
```powershell
# Terminal 1: API
python -m src.api.main

# Terminal 2: UI
python -m src.ui.gradio_interface
```

### Access the System

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **UI**: http://localhost:7860

## Troubleshooting

### PowerShell Script Execution Error
```powershell
# Error: "cannot be loaded because running scripts is disabled"
# Solution: Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found
```powershell
# Add Python to PATH manually:
# 1. Search "Environment Variables" in Start Menu
# 2. Click "Environment Variables"
# 3. Under "System Variables", select "Path"
# 4. Click "Edit"
# 5. Click "New" and add: C:\Users\YourName\AppData\Local\Programs\Python\Python311
# 6. Click "New" and add: C:\Users\YourName\AppData\Local\Programs\Python\Python311\Scripts
# 7. Click OK and restart terminal
```

### PostgreSQL Connection Error
```powershell
# Error: "could not connect to server"
# Solution 1: Check if PostgreSQL is running
# Open Services (services.msc)
# Find "postgresql-x64-15"
# Right-click → Start

# Solution 2: Check connection settings in .env
# Verify DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
```

### Redis Connection Error
```powershell
# Error: "Connection refused"
# Solution: Start Redis service
# Open Services (services.msc)
# Find "Redis"
# Right-click → Start

# Or restart Redis:
net stop Redis
net start Redis
```

### OpenSearch Connection Error
```powershell
# If using Docker:
docker ps  # Check if OpenSearch container is running

# Restart container:
docker restart opensearch

# Check logs:
docker logs opensearch
```

### Ollama Not Found
```powershell
# Error: "ollama: command not found"
# Solution: Restart computer after installing Ollama
# Or add to PATH manually:
# C:\Users\YourName\AppData\Local\Programs\Ollama
```

### Port Already in Use
```powershell
# Error: "Address already in use"
# Find process using port:
netstat -ano | findstr :8000

# Kill process:
taskkill /PID <PID> /F

# Replace <PID> with the number from netstat output
```

### Module Not Found Error
```powershell
# Error: "No module named 'xyz'"
# Solution: Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### SSL Certificate Error
```powershell
# Error during pip install
# Solution: Use trusted hosts
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

## Performance Tips

### 1. Use SSD for Database
- Install PostgreSQL on SSD for better performance
- Store OpenSearch data on SSD

### 2. Increase Memory Limits

Edit `.env`:
```bash
# For OpenSearch
OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g

# For PostgreSQL
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=20
```

### 3. Enable Windows Features
```powershell
# Enable Windows Subsystem for Linux (optional)
wsl --install

# Helps with Docker performance
```

### 4. Disable Antivirus Scanning

Add project folder to antivirus exclusions:
- Open Windows Security
- Virus & threat protection
- Manage settings
- Add exclusions
- Add folder: `C:\Projects\research-paper-curator`

## Development Tips

### Use VS Code

1. Install VS Code: https://code.visualstudio.com/
2. Install Python extension
3. Open project: `code .`
4. Select Python interpreter: Ctrl+Shift+P → "Python: Select Interpreter" → Choose `.\venv\Scripts\python.exe`

### Use Windows Terminal

Better terminal experience:
- Install from Microsoft Store
- Set as default terminal
- Supports tabs and panes

### Git Configuration
```powershell
# Configure line endings
git config --global core.autocrlf true

# Set default editor
git config --global core.editor "code --wait"
```

## Next Steps

1. ✓ System is running
2. Try the web UI: http://localhost:7860
3. Test API: http://localhost:8000/docs
4. Read [API Documentation](API.md)
5. Check [Architecture Guide](ARCHITECTURE.md)

## Getting Help

- **Documentation**: `/docs` folder
- **Issues**: GitHub Issues
- **Discord**: [Join our community]
- **Email**: support@example.com

---

**Need more help?** Create an issue on GitHub with:
- Error message
- Steps to reproduce
- System information (`winver` output)
- Logs from `logs/` folder