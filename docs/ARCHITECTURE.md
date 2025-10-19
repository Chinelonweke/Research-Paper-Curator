# System Architecture

Comprehensive architecture documentation for the Research Paper Curator RAG system.

## Table of Contents

- [Overview](#overview)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Design Decisions](#design-decisions)
- [Scalability](#scalability)
- [Security](#security)

## Overview

The Research Paper Curator is a production-ready RAG (Retrieval-Augmented Generation) system that enables users to query and explore AI research papers through natural language questions.

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                           │
│  ┌────────────────────┐         ┌────────────────────┐         │
│  │   Gradio Web UI    │         │   REST API Clients │         │
│  │   (Port 7860)      │         │                    │         │
│  └──────────┬─────────┘         └──────────┬─────────┘         │
└─────────────┼────────────────────────────────┼─────────────────┘
              │                                │
              ▼                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API Layer (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Route Handlers                         │  │
│  │  /ask  /search  /papers  /ingest  /health  /stats       │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  ┌────────────────────────┼─────────────────────────────────┐  │
│  │              Business Logic Layer                        │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │  │
│  │  │  Q&A    │  │ Search  │  │ Ingest  │  │  Cache  │   │  │
│  │  │ Service │  │ Service │  │ Service │  │ Manager │   │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │  │
│  └────────────────────────┬─────────────────────────────────┘  │
└───────────────────────────┼─────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│    Data Access Layer    │   │   Integration Layer     │
│  ┌──────────────────┐   │   │  ┌──────────────────┐  │
│  │  Database ORM    │   │   │  │  Embedding Gen   │  │
│  │  (SQLAlchemy)    │   │   │  │  (Sentence-T)    │  │
│  └──────────────────┘   │   │  └──────────────────┘  │
│  ┌──────────────────┐   │   │  ┌──────────────────┐  │
│  │  OpenSearch      │   │   │  │  LLM Client      │  │
│  │  Client          │   │   │  │  (Ollama)        │  │
│  └──────────────────┘   │   │  └──────────────────┘  │
│  ┌──────────────────┐   │   │  ┌──────────────────┐  │
│  │  Redis Client    │   │   │  │  arXiv Fetcher   │  │
│  └──────────────────┘   │   │  └──────────────────┘  │
└─────────────────────────┘   └─────────────────────────┘
              │                           │
              └───────────┬───────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Infrastructure Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ PostgreSQL  │  │ OpenSearch  │  │   Redis     │            │
│  │  (Port 5432)│  │ (Port 9200) │  │ (Port 6379) │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│  ┌─────────────┐  ┌─────────────┐                              │
│  │   Ollama    │  │  Airflow    │                              │
│  │ (Port 11434)│  │ (Port 8080) │                              │
│  └─────────────┘  └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

## System Components

### 1. Frontend Layer

#### Gradio Web UI
- **Purpose**: User-friendly interface for asking questions and browsing papers
- **Technology**: Gradio 4.16+
- **Features**:
  - Question answering interface
  - Paper search and filtering
  - System statistics dashboard
  - Real-time health monitoring
- **Communication**: REST API calls to FastAPI backend

#### API Clients
- Direct API access for programmatic usage
- Supports curl, Python requests, JavaScript fetch
- Authentication ready (extensible)

### 2. API Layer (FastAPI)

#### Core Components

**Route Handlers** (`src/api/routes.py`)
- `/api/v1/ask` - Question answering endpoint
- `/api/v1/search` - Paper search endpoint
- `/api/v1/papers` - Paper management
- `/api/v1/ingest` - Data ingestion triggers
- `/api/v1/health` - Health checks
- `/api/v1/stats` - System statistics

**Middleware Stack**
- CORS handling
- Request logging
- Error handling
- Rate limiting (extensible)
- Authentication (extensible)

**Dependency Injection** (`src/api/dependencies.py`)
- Database session management
- Service initialization
- Component lifecycle management

### 3. Business Logic Layer

#### Question Answering Service

**Pipeline Flow:**
```python
1. Receive Question
   ↓
2. Check Cache (Redis)
   ↓ (miss)
3. Generate Query Embedding
   ↓
4. Hybrid Search (Vector + BM25)
   ↓
5. Rerank Results
   ↓
6. Generate Answer (LLM)
   ↓
7. Cache Result
   ↓
8. Return Answer + Sources
```

**Implementation:**
- Async/await for non-blocking I/O
- Error handling with retries
- Timeout management
- Observability tracking (Langfuse)

#### Search Service

**Hybrid Search Algorithm:**
```python
def hybrid_search(query, top_k, alpha=0.5):
    # 1. Vector Search (Semantic)
    query_embedding = embedding_model.encode(query)
    vector_results = opensearch.knn_search(
        embedding=query_embedding,
        k=top_k * 2
    )
    
    # 2. Keyword Search (Lexical)
    keyword_results = opensearch.bm25_search(
        query=query,
        k=top_k * 2
    )
    
    # 3. Reciprocal Rank Fusion
    merged = reciprocal_rank_fusion(
        vector_results,
        keyword_results,
        alpha=alpha,
        k=60
    )
    
    return merged[:top_k]
```

**Why Hybrid Search?**
- Vector search captures semantic similarity
- BM25 captures exact keyword matches
- RRF combines strengths of both
- Configurable alpha balances contributions

#### Ingestion Service

**Processing Pipeline:**
```
arXiv API
    ↓
Fetch Papers
    ↓
Store Metadata (PostgreSQL)
    ↓
Chunk Text (500 words, 50 overlap)
    ↓
Generate Embeddings (384-dim)
    ↓
Index in OpenSearch
    ↓
Update Status
```

**Chunking Strategy:**
- Chunk size: 500 words
- Overlap: 50 words (context preservation)
- Types: title, abstract, introduction, methods
- Max chunks per paper: 50

### 4. Data Access Layer

#### Database Schema (PostgreSQL)
```sql
-- Papers table
CREATE TABLE papers (
    id SERIAL PRIMARY KEY,
    arxiv_id VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    abstract TEXT NOT NULL,
    authors TEXT[] NOT NULL,
    categories TEXT[] NOT NULL,
    published_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    indexed TIMESTAMP,
    INDEX idx_arxiv_id (arxiv_id),
    INDEX idx_categories (categories),
    INDEX idx_published (published_date)
);

-- Chunks table
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    chunk_type VARCHAR(50),
    token_count INTEGER,
    embedding_indexed TIMESTAMP,
    INDEX idx_paper_chunk (paper_id, chunk_index)
);

-- Search logs
CREATE TABLE search_logs (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    top_k INTEGER,
    processing_time_ms FLOAT,
    num_results INTEGER,
    cache_hit INTEGER,
    timestamp TIMESTAMP DEFAULT NOW(),
    INDEX idx_timestamp (timestamp)
);
```

#### OpenSearch Index Mapping
```json
{
  "mappings": {
    "properties": {
      "chunk_id": {"type": "integer"},
      "paper_id": {"type": "integer"},
      "arxiv_id": {"type": "keyword"},
      "content": {"type": "text"},
      "paper_title": {"type": "text"},
      "paper_authors": {"type": "text"},
      "paper_categories": {"type": "keyword"},
      "published_date": {"type": "date"},
      "embedding": {
        "type": "knn_vector",
        "dimension": 384,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "nmslib",
          "parameters": {
            "ef_construction": 128,
            "m": 16
          }
        }
      }
    }
  }
}
```

### 5. Integration Layer

#### Embedding Generation
- **Model**: all-MiniLM-L6-v2
- **Dimension**: 384
- **Framework**: Sentence Transformers
- **Batch size**: 32
- **Normalization**: L2 (for cosine similarity)

#### LLM Integration (Ollama)
- **Default Model**: Llama 2 7B
- **API**: REST (local)
- **Context window**: 4096 tokens
- **Temperature**: 0.3 (for factual QA)
- **Streaming**: Supported

#### arXiv Integration
- **API**: arXiv.org API
- **Rate limit**: 3 seconds between requests
- **Categories**: cs.AI, cs.CL, cs.CV, cs.LG
- **Max results per request**: 100

### 6. Infrastructure Layer

#### PostgreSQL Configuration
```yaml
Version: 15+
Max Connections: 100
Shared Buffers: 256MB
Effective Cache: 1GB
Maintenance Work Mem: 128MB
WAL Buffers: 16MB
```

#### OpenSearch Configuration
```yaml
Version: 2.11+
Heap Size: 512MB - 2GB
Shards: 2
Replicas: 1
Index Refresh Interval: 1s
KNN Plugin: Enabled
```

#### Redis Configuration
```yaml
Version: 7+
Max Memory: 256MB
Eviction Policy: allkeys-lru
Persistence: AOF
AOF Sync: everysec
```

## Data Flow

### Question Answering Flow
```
User Question
    ↓
┌───────────────────────────┐
│ 1. API Receives Request   │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ 2. Check Redis Cache      │
│    Cache Key: hash(query) │
└───────────────────────────┘
    ↓ (cache miss)
┌───────────────────────────┐
│ 3. Generate Embedding     │
│    Input: Query text      │
│    Output: 384-dim vector │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ 4. Hybrid Search          │
│    a. Vector Search (KNN) │
│    b. BM25 Search         │
│    c. RRF Merge           │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ 5. Build Context          │
│    Top K chunks           │
│    Paper metadata         │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ 6. LLM Generation         │
│    System: QA prompt      │
│    User: Context + Query  │
│    Temp: 0.3              │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ 7. Format Response        │
│    Answer + Sources       │
│    Metadata + Timing      │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ 8. Cache Result           │
│    TTL: 1 hour            │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ 9. Log Metrics            │
│    Search log to DB       │
│    Langfuse trace         │
└───────────────────────────┘
    ↓
Return to User
```

### Ingestion Flow
```
Airflow Scheduler (Daily 2 AM)
    ↓
┌───────────────────────────┐
│ 1. Fetch from arXiv       │
│    Query: Last 24h        │
│    Categories: cs.*       │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ 2. Check Duplicates       │
│    Query: arxiv_id in DB  │
└───────────────────────────┘
    ↓ (new papers)
┌───────────────────────────┐
│ 3. Store Metadata         │
│    Insert into PostgreSQL │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ 4. Text Chunking          │
│    Size: 500 words        │
│    Overlap: 50 words      │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ 5. Generate Embeddings    │
│    Batch: 32 chunks       │
│    Model: MiniLM          │
└───────────────────────────┐
    ↓
┌───────────────────────────┐
│ 6. Index in OpenSearch    │
│    Bulk index operation   │
│    Update chunks table    │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ 7. Update Status          │
│    Mark as indexed        │
│    Log statistics         │
└───────────────────────────┘
```

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **API Framework** | FastAPI | 0.109+ | High-performance async API |
| **UI Framework** | Gradio | 4.16+ | Rapid UI development |
| **Vector DB** | OpenSearch | 2.11+ | Vector similarity search |
| **Database** | PostgreSQL | 15+ | Relational data storage |
| **Cache** | Redis | 7+ | High-speed caching |
| **LLM** | Ollama | Latest | Local LLM inference |
| **Embeddings** | Sentence-T | 2.3+ | Text embeddings |
| **Orchestration** | Airflow | 2.8+ | Workflow automation |
| **Monitoring** | Langfuse | 2.17+ | LLM observability |

### Python Dependencies

**Core:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `sqlalchemy` - ORM
- `psycopg2` - PostgreSQL driver

**ML/AI:**
- `sentence-transformers` - Embeddings
- `torch` - Deep learning framework
- `numpy` - Numerical computing

**Search:**
- `opensearch-py` - OpenSearch client
- `rank-bm25` - BM25 algorithm

**Data:**
- `arxiv` - arXiv API client
- `redis` - Redis client
- `apache-airflow` - Workflow orchestration

**Utilities:**
- `python-dotenv` - Environment management
- `loguru` - Logging
- `tenacity` - Retry logic
- `requests` - HTTP client

## Design Decisions

### 1. Why Hybrid Search?

**Problem**: Neither pure vector search nor pure keyword search is optimal alone.

**Solution**: Combine both using Reciprocal Rank Fusion (RRF).

**Benefits:**
- Vector search: Captures semantic meaning
- BM25: Captures exact term matches
- RRF: Balances both methods
- Configurable alpha: Tune for your use case

**Trade-offs:**
- Slightly slower than single method
- Requires two indexes
- More complex implementation

### 2. Why Local LLM (Ollama)?

**Rationale:**
- **Privacy**: Data never leaves your infrastructure
- **Cost**: No API fees
- **Control**: Full control over model and parameters
- **Latency**: No network overhead for inference

**Trade-offs:**
- Requires GPU for good performance
- Smaller models vs. GPT-4
- Self-hosting complexity

**Alternative**: Easily swap to OpenAI API by changing LLM client.

### 3. Why PostgreSQL + OpenSearch?

**PostgreSQL:**
- Structured metadata storage
- ACID transactions
- Mature ecosystem
- Complex queries and joins

**OpenSearch:**
- Fast vector similarity search
- Full-text search with BM25
- Horizontal scalability
- Rich query DSL

**Why both?**
- Different strengths for different data
- PostgreSQL: Source of truth for metadata
- OpenSearch: Fast retrieval and search

### 4. Why Redis Caching?

**Benefits:**
- 100x faster than database queries
- Reduces LLM API calls
- Improves response time
- Lower infrastructure costs

**Cache Strategy:**
- Cache key: Hash of query + parameters
- TTL: 1 hour (configurable)
- Eviction: LRU (Least Recently Used)

### 5. Chunking Strategy

**Configuration:**
```python
CHUNK_SIZE = 500  # words
CHUNK_OVERLAP = 50  # words
MAX_CHUNKS = 50  # per paper
```

**Rationale:**
- 500 words ≈ 700 tokens (fits in context)
- 50-word overlap preserves context
- Max 50 chunks prevents explosion

**Trade-offs:**
- Larger chunks: More context, fewer chunks
- Smaller chunks: More granular, more chunks
- Overlap: Better context, more storage

### 6. Asynchronous Architecture

**Why async?**
- Non-blocking I/O operations
- Handle multiple requests concurrently
- Better resource utilization
- Scalable to thousands of requests

**Implementation:**
- FastAPI: Native async support
- Database: Async drivers (optional)
- Redis: Async client (optional)
- LLM: Streaming support

## Scalability

### Horizontal Scaling

#### API Layer
```yaml
# docker-compose scale
docker-compose up -d --scale api=3

# Behind load balancer (Nginx/Traefik)
upstream api_backend {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}
```

#### Database Layer
```yaml
# Read replicas for search-heavy workloads
Primary: Write operations
Replicas: Read operations (search, list)

# Connection pooling
Pool size: 20 connections per instance
Max overflow: 10
```

#### OpenSearch Cluster
```yaml
# 3-node cluster
opensearch-node1:
  role: master, data
opensearch-node2:
  role: data
opensearch-node3:
  role: data

# Index sharding
Shards: 3
Replicas: 2
```

### Vertical Scaling

**API Server:**
- CPU: 4+ cores
- RAM: 8GB+
- Workers: 4-8 (2x CPU cores)

**Database:**
- CPU: 4+ cores
- RAM: 16GB+
- Storage: SSD required

**OpenSearch:**
- CPU: 4+ cores
- RAM: 8GB+ (4GB heap)
- Storage: SSD required

**Redis:**
- CPU: 2+ cores
- RAM: 4GB+
- Persistence: AOF enabled

### Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| API Latency (cached) | < 50ms | P95 |
| API Latency (uncached) | < 2s | P95, with LLM |
| Search Latency | < 200ms | P95 |
| Embedding Generation | < 100ms | Per text |
| LLM Generation | < 1.5s | For 200 tokens |
| Throughput | 100+ RPS | Per API instance |
| Concurrent Users | 500+ | With 3 API instances |

### Optimization Strategies

1. **Database Indexing**
   - B-tree indexes on foreign keys
   - GiST indexes on arrays
   - Partial indexes on frequent queries

2. **Caching Strategy**
   - L1: In-memory cache (LRU, 100 items)
   - L2: Redis cache (1 hour TTL)
   - L3: Database query

3. **Connection Pooling**
   - Database: SQLAlchemy pool
   - Redis: Connection pool
   - HTTP: Session reuse

4. **Batch Processing**
   - Embeddings: Batch of 32
   - Database inserts: Bulk operations
   - OpenSearch: Bulk indexing

5. **Query Optimization**
   - Select only needed columns
   - Use joins instead of N+1 queries
   - Paginate large result sets

## Security

### Authentication & Authorization

**Current State**: Open (development)

**Production Recommendations**:
```python
# JWT token-based auth
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/api/v1/ask")
async def ask_question(
    request: QuestionRequest,
    token: str = Depends(oauth2_scheme)
):
    # Verify token
    user = verify_token(token)
    # Process request
    ...
```

### Data Security

**At Rest:**
- Database encryption: PostgreSQL encryption extensions
- Disk encryption: LUKS (Linux) / BitLocker (Windows)

**In Transit:**
- HTTPS/TLS for all API endpoints
- Certificate management: Let's Encrypt

**API Security:**
- Rate limiting: 100 requests/minute per IP
- Input validation: Pydantic models
- SQL injection prevention: SQLAlchemy ORM
- XSS prevention: FastAPI automatic escaping

### Infrastructure Security

**Network:**
```yaml
# Firewall rules
Inbound:
  - Allow 443 (HTTPS)
  - Allow 80 (HTTP, redirect to HTTPS)
  - Block all other ports

Internal:
  - Database: Only from API servers
  - Redis: Only from API servers
  - OpenSearch: Only from API servers
```

**Access Control:**
- Principle of least privilege
- Separate service accounts
- No root access in containers
- Read-only file systems where possible

**Secrets Management:**
- Environment variables for secrets
- No secrets in code or git
- Use secret management tools (Vault, AWS Secrets Manager)

### Monitoring & Auditing

**Logging:**
- All API requests logged
- Failed authentication attempts
- Database queries (in debug mode)
- Error stack traces

**Metrics:**
- Request rates and latencies
- Error rates
- Resource utilization
- Cache hit rates

**Alerting:**
- High error rates
- Service downtime
- Resource exhaustion
- Security anomalies

## Disaster Recovery

### Backup Strategy

**Database:**
```bash
# Daily backups
pg_dump research_papers > backup_$(date +%Y%m%d).sql

# Retention: 30 days
# Storage: S3 / Azure Blob
```

**OpenSearch:**
```bash
# Snapshot to S3
curl -X PUT "localhost:9200/_snapshot/backup/snapshot_$(date +%Y%m%d)"

# Retention: 7 days
```

**Configuration:**
- Git repository for code
- Backup `.env` securely
- Document recovery procedures

### Recovery Procedures

1. **Database Recovery**
```bash
   psql research_papers < backup_20231201.sql
```

2. **OpenSearch Recovery**
```bash
   curl -X POST "localhost:9200/_snapshot/backup/snapshot_20231201/_restore"
```

3. **Application Recovery**
```bash
   git checkout <stable-commit>
   docker-compose up -d
```

---

**Architecture maintained by**: Your Team
**Last updated**: 2025-10-14
**Version**: 1.0.0