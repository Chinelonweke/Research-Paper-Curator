# API Documentation

Complete REST API reference for the Research Paper Curator system.

## Base URL
```
Development: http://localhost:8000
Production: https://api.yourcompany.com
```

## Authentication

Currently, the API is open for development. For production:
```http
Authorization: Bearer <your_token_here>
```

## API Versioning

All endpoints are versioned under `/api/v1/`.

## Rate Limiting

- **Development**: No limits
- **Production**: 100 requests/minute per IP

## Response Format

### Success Response
```json
{
  "status": "success",
  "data": { ... }
}
```

### Error Response
```json
{
  "detail": "Error message here",
  "status_code": 400
}
```

## Endpoints

### Health & Status

#### GET /health

Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "api": "operational",
    "database": "pending",
    "cache": "pending"
  }
}
```

#### GET /api/v1/health/detailed

Detailed health check with component status.

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "opensearch": "healthy",
    "ollama": "healthy"
  },
  "timestamp": "2025-10-14T10:30:00Z"
}
```

---

### Question Answering

#### POST /api/v1/ask

Ask a question about research papers.

**Request Body:**
```json
{
  "question": "What are transformers in NLP?",
  "top_k": 5,
  "use_cache": true,
  "filter_categories": ["cs.AI", "cs.CL"],
  "user_id": "user_123",
  "session_id": "session_456"
}
```

**Parameters:**
- `question` (string, required): The question to ask (1-1000 chars)
- `top_k` (integer, optional): Number of sources to retrieve (1-20, default: 5)
- `use_cache` (boolean, optional): Whether to use cached results (default: true)
- `filter_categories` (array, optional): Filter papers by categories
- `user_id` (string, optional): User identifier for tracking
- `session_id` (string, optional): Session identifier for tracking

**Response:**
```json
{
  "question": "What are transformers in NLP?",
  "answer": "Transformers are a type of neural network architecture...",
  "sources": [
    {
      "arxiv_id": "1706.03762",
      "paper_title": "Attention Is All You Need",
      "paper_authors": ["Vaswani", "Shazeer", "Parmar"],
      "chunk_content": "The Transformer model architecture...",
      "relevance_score": 0.9234,
      "chunk_type": "abstract"
    }
  ],
  "processing_time_ms": 1234.56,
  "cache_hit": false,
  "metadata": {
    "search_latency_ms": 234.56,
    "llm_latency_ms": 987.65,
    "num_sources": 5,
    "model": "llama2"
  }
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: No relevant papers found
- `422 Unprocessable Entity`: Invalid input
- `500 Internal Server Error`: Server error

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are transformers in NLP?",
    "top_k": 5
  }'
```

---

### Search

#### GET /api/v1/search

Search for papers without generating an answer.

**Query Parameters:**
- `query` (string, required): Search query
- `top_k` (integer, optional): Number of results (1-50, default: 10)
- `search_type` (string, optional): Type of search: "vector", "keyword", or "hybrid" (default: "hybrid")

**Response:**
```json
{
  "query": "attention mechanism",
  "results": [
    {
      "arxiv_id": "1706.03762",
      "paper_title": "Attention Is All You Need",
      "paper_authors": ["Vaswani", "Shazeer"],
      "chunk_content": "We propose a new architecture...",
      "relevance_score": 0.9234,
      "paper_categories": ["cs.CL", "cs.LG"]
    }
  ],
  "total_results": 25,
  "processing_time_ms": 123.45
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/search?query=attention%20mechanism&top_k=10"
```

---

### Papers

#### GET /api/v1/papers

List papers with pagination and filtering.

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum records to return (1-100, default: 20)
- `category` (string, optional): Filter by category (e.g., "cs.AI")

**Response:**
```json
[
  {
    "id": 1,
    "arxiv_id": "1706.03762",
    "title": "Attention Is All You Need",
    "authors": ["Ashish Vaswani", "Noam Shazeer"],
    "abstract": "The dominant sequence transduction models...",
    "categories": ["cs.CL", "cs.LG"],
    "published_date": "2017-06-12T00:00:00Z",
    "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf"
  }
]
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/papers?limit=20&category=cs.AI"
```

#### GET /api/v1/papers/{arxiv_id}

Get detailed information about a specific paper.

**Path Parameters:**
- `arxiv_id` (string): arXiv ID of the paper

**Response:**
```json
{
  "id": 1,
  "arxiv_id": "1706.03762",
  "title": "Attention Is All You Need",
  "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
  "abstract": "The dominant sequence transduction models...",
  "categories": ["cs.CL", "cs.LG"],
  "published_date": "2017-06-12T00:00:00Z",
  "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf",
  "comment": "NIPS 2017",
  "journal_ref": null,
  "doi": null,
  "primary_category": "cs.CL",
  "created_at": "2025-01-01T10:00:00Z",
  "indexed": "2025-01-01T10:05:00Z"
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Paper not found

**Example:**
```bash
curl "http://localhost:8000/api/v1/papers/1706.03762"
```

---

### Data Ingestion

#### POST /api/v1/ingest/recent

Ingest recent papers from arXiv (background task).

**Query Parameters:**
- `days_back` (integer, optional): Number of days to look back (1-30, default: 7)
- `max_results` (integer, optional): Maximum papers to fetch (1-200, default: 50)

**Response:**
```json
{
  "status": "started",
  "message": "Ingestion started in background for last 7 days",
  "max_results": 50
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/recent?days_back=7&max_results=50"
```

#### POST /api/v1/ingest/paper/{arxiv_id}

Ingest a specific paper by arXiv ID.

**Path Parameters:**
- `arxiv_id` (string): arXiv ID of the paper

**Response:**
```json
{
  "status": "success",
  "arxiv_id": "1706.03762",
  "result": "new"
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Paper not found on arXiv
- `500 Internal Server Error`: Processing error

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/paper/1706.03762"
```

---

### System Statistics

#### GET /api/v1/stats

Get system statistics.

**Response:**
```json
{
  "total_papers": 1234,
  "indexed_papers": 1230,
  "total_chunks": 15420,
  "opensearch_documents": 15420,
  "opensearch_size_mb": 245.67
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/stats"
```

---

### Cache Management

#### GET /api/v1/cache/stats

Get cache statistics.

**Response:**
```json
{
  "hits": 1234,
  "misses": 567,
  "hit_rate": 68.52,
  "total_keys": 450,
  "used_memory_human": "12.5MB",
  "connected_clients": 3
}
```

#### DELETE /api/v1/cache/clear

Clear cache (all or by pattern).

**Query Parameters:**
- `pattern` (string, optional): Pattern to match (e.g., "search:*")

**Response:**
```json
{
  "status": "success",
  "cleared": 125,
  "pattern": "search:*"
}
```

**Example:**
```bash
# Clear all cache
curl -X DELETE "http://localhost:8000/api/v1/cache/clear"

# Clear search cache only
curl -X DELETE "http://localhost:8000/api/v1/cache/clear?pattern=search:*"
```

---

## Error Codes

| Status Code | Meaning |
|-------------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - Service down |

## SDKs & Libraries

### Python
```python
import requests

class RAGClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def ask(self, question, top_k=5):
        response = requests.post(
            f"{self.base_url}/api/v1/ask",
            json={"question": question, "top_k": top_k}
        )
        return response.json()
    
    def search(self, query, top_k=10):
        response = requests.get(
            f"{self.base_url}/api/v1/search",
            params={"query": query, "top_k": top_k}
        )
        return response.json()

# Usage
client = RAGClient()
result = client.ask("What are transformers?")
print(result["answer"])
```

### JavaScript
```javascript
class RAGClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async ask(question, topK = 5) {
    const response = await fetch(`${this.baseURL}/api/v1/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, top_k: topK })
    });
    return response.json();
  }

  async search(query, topK = 10) {
    const params = new URLSearchParams({ query, top_k: topK });
    const response = await fetch(`${this.baseURL}/api/v1/search?${params}`);
    return response.json();
  }
}

// Usage
const client = new RAGClient();
const result = await client.ask('What are transformers?');
console.log(result.answer);
```

## WebSocket Support

*Coming in v2.0*

Real-time streaming of LLM responses:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/stream');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.chunk); // Partial response
};

ws.send(JSON.stringify({
  question: "What are transformers?",
  top_k: 5
}));
```

## Interactive Documentation

Visit these URLs for interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

**API Version**: v1
**Last Updated**: 2025-10-14
**Support**: api-support@yourcompany.com