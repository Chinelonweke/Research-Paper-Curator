# 📚 Research Paper Curator - Complete RAG System

A production-ready Retrieval-Augmented Generation (RAG) system for curating, searching, and querying AI research papers from arXiv.

[![CI Pipeline](https://github.com/yourusername/research-paper-curator/workflows/CI%20Pipeline/badge.svg)](https://github.com/yourusername/research-paper-curator/actions)
[![codecov](https://codecov.io/gh/yourusername/research-paper-curator/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/research-paper-curator)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## 🌟 Features

### Core Functionality
- **🤖 Intelligent Q&A**: Ask questions about AI research and get accurate answers with citations.
- **🔍 Hybrid Search**: Combines semantic vector similarity and keyword search for optimal results.
- **🖼️ Premium Glassmorphism UI**: High-end, interactive web interface with modern blurring and micro-animations.
- **🌑 Monochrome Branding**: Sophisticated black-core aesthetic for a professional, distraction-free environment.
- **📄 Paper Management**: Automatic fetching, processing, and indexing of arXiv papers.
- **🚀 High Performance**: Redis caching and optimized search response times.

### Technical Highlights
- **Retrieval-Augmented Generation (RAG)** architecture
- **Hybrid Search** with BM25 and vector similarity (cosine)
- **Local LLM** support via Ollama (privacy-focused)
- **Vector Database** with OpenSearch for semantic search
- **PostgreSQL** for structured data and metadata
- **Redis** for caching and performance optimization
- **Apache Airflow** for automated data ingestion
- **Langfuse** for LLM observability and monitoring
- **Docker** support for easy deployment
- **CI/CD** pipeline with GitHub Actions

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Deployment](#-deployment)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 15+
- Redis 7+
- OpenSearch 2.11+
- Ollama (for LLM)
- Docker (optional, for containerized deployment)

### Quick Installation (Windows)
```powershell
# 1. Clone repository
git clone https://github.com/yourusername/research-paper-curator.git
cd research-paper-curator

# 2. Run setup script
powershell -ExecutionPolicy Bypass -File scripts/setup_windows.ps1

# 3. Configure environment
# Edit .env file with your settings

# 4. Start services with Docker
docker-compose -f docker/docker-compose.yml up -d

# 5. Initialize database
python scripts/setup_db.py

# 6. Seed sample data
python scripts/seed_data.py

# 7. Access the system
# API: http://localhost:8000
# UI: http://localhost:3000
# Airflow: http://localhost:8080
```

### Quick Installation (Linux/Mac)
```bash
# 1. Clone repository
git clone https://github.com/yourusername/research-paper-curator.git
cd research-paper-curator

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
make dev-install

# 4. Configure environment
pip install -r requirements.txt
# Edit .env file

# 5. Start services with Docker
docker-compose -f docker/docker-compose.yml up -d

# 6. Initialize database
python scripts/setup_db.py

# 7. Seed data
python scripts/seed_data.py

# 8. Run the application (Local Dev)
# Backend: python -m src.api.main
# Frontend: cd frontend && npm run dev
```

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
│                     (Gradio Web UI / API)                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Question   │  │    Search    │  │   Ingestion  │     │
│  │  Answering   │  │   Engine     │  │   Pipeline   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────────┬────────────────┬────────────────┬──────────────┘
            │                │                │
            ▼                ▼                ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   Ollama     │  │  OpenSearch  │  │  PostgreSQL  │
    │    (LLM)     │  │   (Vector)   │  │  (Metadata)  │
    └──────────────┘  └──────────────┘  └──────────────┘
            │                                    │
            ▼                                    ▼
    ┌──────────────┐                    ┌──────────────┐
    │    Redis     │                    │   Airflow    │
    │  (Caching)   │                    │ (Scheduling) │
    └──────────────┘                    └──────────────┘
```

### Component Overview

| Component | Purpose | Technology |
|-----------|---------|------------|
| **API Layer** | RESTful API endpoints | FastAPI |
| **Frontend** | Modern glassmorphism UI | Vue 3 + Vuetify |
| **Search Engine** | Hybrid retrieval | OpenSearch + BM25 |
| **LLM** | Answer generation | Ollama (Llama 3 / DeepSeek) |
| **Vector Store** | Embeddings storage | OpenSearch |
| **Branding** | Custom Identity | SVG Logo + Monochrome Theme |
| **Cache** | Performance optimization | Redis |
| **Scheduler** | Automated tasks | Apache Airflow |
| **Monitoring** | Observability | Langfuse |

## 📦 Installation

### Option 1: Docker (Recommended)
```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Check status
docker-compose -f docker/docker-compose.yml ps

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

### Option 2: Local Installation

#### Step 1: Install System Dependencies

**Windows:**
- [Python 3.9+](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/windows/)
- [Redis](https://github.com/microsoftarchive/redis/releases)
- [Ollama](https://ollama.ai)

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv postgresql-15 redis-server
```

**macOS:**
```bash
brew install python@3.11 postgresql@15 redis ollama
```

#### Step 2: Install Python Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Configure Services

**PostgreSQL:**
```bash
# Create database
createdb research_papers

# Set password (edit .env file)
```

**Redis:**
```bash
# Start Redis
redis-server

# Or as service (Linux)
sudo systemctl start redis
```

**Ollama:**
```bash
# Pull model
ollama pull llama2

# Verify
ollama list
```

**OpenSearch:**
```bash
# Using Docker
docker run -d -p 9200:9200 -e "discovery.type=single-node" \
  -e "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m" \
  opensearchproject/opensearch:2.11.0
```

## ⚙️ Configuration

### Environment Variables

Create `.env` file from template:
```bash
cp .env.example .env
```

Key configuration options:
```bash
# Application
APP_NAME="Research Paper Curator"
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=research_papers
DB_USER=postgres
DB_PASSWORD=your_password

# OpenSearch
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2

# API
API_HOST=0.0.0.0
API_PORT=8000

# UI
UI_PORT=7860
UI_SHARE=false
```

See `.env.example` for all options.

## 📖 Usage

### Starting the System

**Windows:**
```powershell
# Using PowerShell Makefile
.\Makefile.ps1 run-all

# Or manually
# Terminal 1: API
python -m src.api.main

# Terminal 2: UI
cd frontend; npm run dev
```

**Multi-terminal / Manual:**

# Terminal 1: API/Backend
python -m src.api.main

# Terminal 2: UI/Frontend
cd frontend && npm run dev

### Using the Web Interface

1. Open browser to `http://localhost:3000`
2. Explore the **Landing Page** with dynamic particle background
3. Navigate to **Ask** to synthesize answers from multiple papers
4. Check **Browse** to view the full library with interactive glass cards
5. Use **Search** for deep hybrid exploration
6. Access your **History & Analytics** to re-run past discoveries

### Using the API

**Ask a Question:**
```bash
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are transformers in NLP?",
    "top_k": 5
  }'
```

**Search Papers:**
```bash
curl "http://localhost:8000/api/v1/search?query=attention%20mechanism&top_k=10"
```

**List Papers:**
```bash
curl "http://localhost:8000/api/v1/papers?limit=20&category=cs.AI"
```

**Health Check:**
```bash
curl "http://localhost:8000/api/v1/health/detailed"
```

See [API Documentation](docs/API.md) for complete API reference.

## 🔧 Development

### Project Structure
```
research-paper-curator/
├── src/                    # Source code
│   ├── api/               # FastAPI application
│   ├── core/              # Configuration and logging
│   ├── database/          # Database models and operations
│   ├── embeddings/        # Embedding generation
│   ├── retrieval/         # Search engines
│   ├── llm/              # LLM integration
│   ├── ingestion/        # Data processing
│   ├── cache/            # Redis caching
│   ├── monitoring/       # Observability
│   └── ui/               # Gradio interface
├── airflow/              # Airflow DAGs
├── tests/                # Test suite
├── scripts/              # Utility scripts
├── docker/               # Docker configuration
└── docs/                 # Documentation
```

### Running Tests
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit

# Integration tests
pytest tests/integration

# With coverage
pytest --cov=src --cov-report=term-missing
```

### Code Quality
```bash
# Format / Lint code
# Backend: ruff check . --fix
# Frontend: cd frontend && npm run lint
```

### Adding New Features

1. Create feature branch
2. Implement feature with tests
3. Run code quality checks
4. Submit pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 🚢 Deployment

### Docker Deployment
```bash
# Build images
docker-compose -f docker/docker-compose.yml build

# Start services
docker-compose -f docker/docker-compose.yml up -d

# Scale services
docker-compose -f docker/docker-compose.yml up -d --scale api=3
```

### Production Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for:
- Production configuration
- Security hardening
- Performance tuning
- Monitoring setup
- Backup strategies

## 🧪 Testing

### Test Coverage

Current coverage: **85%+**
```bash
# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **End-to-End Tests**: Complete workflow testing

## 📊 Monitoring

### Available Metrics

- API latency and throughput
- Search performance
- LLM generation time
- Cache hit rates
- Database query performance
- System resource usage

### Monitoring Tools

- **Langfuse**: LLM observability
- **Prometheus**: Metrics collection (optional)
- **Grafana**: Visualization (optional)

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Gradio](https://gradio.app/)
- [OpenSearch](https://opensearch.org/)
- [Ollama](https://ollama.ai/)
- [Sentence Transformers](https://www.sbert.net/)
- [Apache Airflow](https://airflow.apache.org/)
- [arXiv](https://arxiv.org/)

## 📧 Contact

Your Name - [ @nelonweke](https://x.com/nelonweke?s=21) - nwekechinelo25@yahoo.com
Your Name - [@ebukagaus](https://twitter.com/ebukagaus) - ebulamicheal@gmail.com


---

<p align="center">Made with ❤️ for AI Research</p>