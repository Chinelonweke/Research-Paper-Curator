# Deployment Guide

Comprehensive deployment guide for the Research Paper Curator system.

## Table of Contents

- [Deployment Options](#deployment-options)
- [Prerequisites](#prerequisites)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Production Configuration](#production-configuration)
- [Monitoring & Observability](#monitoring--observability)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

## Deployment Options

### 1. Docker Compose (Recommended for Single Server)

**Pros:**
- Quick setup
- All services containerized
- Easy to manage
- Good for small to medium deployments

**Cons:**
- Single point of failure
- Limited scalability

### 2. Kubernetes (Recommended for Production)

**Pros:**
- Highly scalable
- Auto-healing
- Load balancing
- Rolling updates

**Cons:**
- Complex setup
- Requires k8s knowledge

### 3. Cloud Managed Services

**Pros:**
- Fully managed
- Auto-scaling
- High availability

**Cons:**
- Higher cost
- Vendor lock-in

## Prerequisites

### Hardware Requirements

**Minimum (Development):**
- CPU: 4 cores
- RAM: 16 GB
- Storage: 50 GB SSD
- Network: 100 Mbps

**Recommended (Production):**
- CPU: 8+ cores
- RAM: 32 GB
- Storage: 200 GB SSD (with RAID)
- Network: 1 Gbps

### Software Requirements

- Docker 24.0+
- Docker Compose 2.20+
- SSL Certificate (for HTTPS)
- Domain name (for production)

## Docker Deployment

### Step 1: Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

### Step 2: Clone Repository
```bash
cd /opt
sudo git clone https://github.com/yourusername/research-paper-curator.git
cd research-paper-curator
```

### Step 3: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
sudo nano .env
```

**Production .env Configuration:**
```bash
# Application
APP_NAME="Research Paper Curator"
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Security
SECRET_KEY="generate-strong-random-key-here"
ALLOWED_ORIGINS="https://yourdomain.com,https://api.yourdomain.com"

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=research_papers
DB_USER=raguser
DB_PASSWORD="strong-password-here"
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=20

# OpenSearch
OPENSEARCH_HOST=opensearch
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD="strong-password-here"

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD="strong-password-here"

# Ollama
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama2

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=8

# UI
UI_PORT=7860
UI_SHARE=false

# Langfuse (Optional)
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Step 4: Generate Secrets
```bash
# Generate strong passwords
openssl rand -base64 32  # For SECRET_KEY
openssl rand -base64 24  # For DB_PASSWORD
openssl rand -base64 24  # For REDIS_PASSWORD
openssl rand -base64 24  # For OPENSEARCH_PASSWORD
```

### Step 5: Build and Start Services
```bash
# Build images
docker-compose -f docker/docker-compose.yml build

# Start services
docker-compose -f docker/docker-compose.yml up -d

# Check status
docker-compose -f docker/docker-compose.yml ps

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

### Step 6: Initialize System
```bash
# Wait for services to be ready (30 seconds)
sleep 30

# Initialize database
docker-compose -f docker/docker-compose.yml exec api python scripts/setup_db.py

# Seed initial data
docker-compose -f docker/docker-compose.yml exec api python scripts/seed_data.py

# Pull Ollama model
docker-compose -f docker/docker-compose.yml exec ollama ollama pull llama2
```

### Step 7: Verify Deployment
```bash
# Check health
curl http://localhost:8000/api/v1/health/detailed

# Test question
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are transformers?", "top_k": 5}'
```

## SSL/TLS Configuration

### Using Nginx Reverse Proxy

**Install Nginx:**
```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

**Nginx Configuration** (`/etc/nginx/sites-available/rag-system`):
```nginx
# HTTP redirect to HTTPS
server {
    listen 80;
    server_name yourdomain.com api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# API Server
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 10M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}

# UI Server
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:7860;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Enable and Start Nginx:**
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/rag-system /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Get SSL certificates
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Cloud Deployment

### AWS Deployment

#### Architecture
```
┌─────────────────────────────────────────────────────┐
│                Application Load Balancer            │
│                (HTTPS, SSL Termination)             │
└────────────┬────────────────────────┬───────────────┘
             │                        │
    ┌────────▼──────┐        ┌───────▼───────┐
    │   ECS Task    │        │   ECS Task    │
    │   (API)       │        │   (UI)        │
    └────────┬──────┘        └───────┬───────┘
             │                        │
    ┌────────▼────────────────────────▼───────────────┐
    │              VPC Private Subnet                 │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
    │  │  RDS     │  │ElastiCache│ │OpenSearch│     │
    │  │PostgreSQL│  │  (Redis)  │ │  Service │     │
    │  └──────────┘  └──────────┘  └──────────┘     │
    └─────────────────────────────────────────────────┘
```

#### Services Used
- **ECS/Fargate**: Container orchestration
- **RDS**: Managed PostgreSQL
- **ElastiCache**: Managed Redis
- **OpenSearch Service**: Managed OpenSearch
- **ALB**: Application Load Balancer
- **ECR**: Docker image registry
- **S3**: Backup storage
- **CloudWatch**: Logging and monitoring

#### Deployment Steps

1. **Create VPC and Subnets**
```bash
aws ec2 create-vpc --cidr-block 10.0.0.0/16
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.2.0/24
```

2. **Create RDS Instance**
```bash
aws rds create-db-instance \
  --db-instance-identifier rag-postgres \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.4 \
  --allocated-storage 100 \
  --master-username admin \
  --master-user-password YourStrongPassword \
  --vpc-security-group-ids sg-xxx \
  --db-subnet-group-name your-subnet-group
```

3. **Create ElastiCache Cluster**
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id rag-redis \
  --cache-node-type cache.t3.medium \
  --engine redis \
  --num-cache-nodes 1 \
  --security-group-ids sg-xxx \
  --cache-subnet-group-name your-subnet-group
```

4. **Create OpenSearch Domain**
```bash
aws opensearch create-domain \
  --domain-name rag-opensearch \
  --engine-version OpenSearch_2.11 \
  --cluster-config InstanceType=t3.medium.search,InstanceCount=2 \
  --ebs-options EBSEnabled=true,VolumeType=gp3,VolumeSize=100 \
  --vpc-options SubnetIds=subnet-xxx,SecurityGroupIds=sg-xxx
```

5. **Push Docker Images to ECR**
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t rag-api -f docker/Dockerfile .
docker tag rag-api:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/rag-api:latest

# Push
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/rag-api:latest
```

6. **Create ECS Task Definition**
```json
{
  "family": "rag-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/rag-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DB_HOST", "value": "rag-postgres.xxx.rds.amazonaws.com"},
        {"name": "REDIS_HOST", "value": "rag-redis.xxx.cache.amazonaws.com"},
        {"name": "OPENSEARCH_HOST", "value": "search-rag-opensearch.xxx.es.amazonaws.com"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/rag-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

7. **Create ECS Service**
```bash
aws ecs create-service \
  --cluster rag-cluster \
  --service-name rag-api-service \
  --task-definition rag-api \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=api,containerPort=8000"
```

### Google Cloud Platform (GCP)

**Services:**
- Cloud Run (containers)
- Cloud SQL (PostgreSQL)
- Memorystore (Redis)
- Vertex AI Search (alternative to OpenSearch)

### Azure

**Services:**
- Azure Container Instances
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Azure Cognitive Search

## Production Configuration

### Environment Variables

**Security:**
```bash
# Strong secret key (32+ characters)
SECRET_KEY=$(openssl rand -base64 32)

# JWT settings (if implementing auth)
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

**Performance:**
```bash
# API workers
API_WORKERS=8  # 2x CPU cores

# Database connection pooling
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# Redis
REDIS_CACHE_TTL=3600
REDIS_MAX_CONNECTIONS=50

# OpenSearch
OPENSEARCH_TIMEOUT=30
```

**Logging:**
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json  # For structured logging
SENTRY_DSN=https://...  # Optional error tracking
```

### Performance Tuning

#### PostgreSQL
```sql
-- postgresql.conf
max_connections = 100
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 4
max_parallel_workers_per_gather = 2
max_parallel_workers = 4
```

#### OpenSearch
```yaml
# opensearch.yml
cluster.name: rag-production
node.name: node-1
path.data: /var/lib/opensearch
path.logs: /var/log/opensearch

network.host: 0.0.0.0
http.port: 9200

discovery.type: single-node

# Memory
bootstrap.memory_lock: true
indices.memory.index_buffer_size: 30%
indices.fielddata.cache.size: 40%

# Thread pools
thread_pool.write.queue_size: 1000
thread_pool.search.queue_size: 1000
```

#### Redis
```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
```

## Monitoring & Observability

### Prometheus & Grafana

**Install Prometheus:**
```bash
docker run -d -p 9090:9090 \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'rag-api'
    static_configs:
      - targets: ['localhost:8000']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:5432']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']
```

**Install Grafana:**
```bash
docker run -d -p 3000:3000 grafana/grafana
```

### Application Metrics

Add to FastAPI app:
```python
from prometheus_fastapi_instrumentator import Instrumentator

@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)
```

### Logging

**Structured Logging:**
```python
# src/core/logging_config.py
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
```

**Log Aggregation** (ELK Stack):
- Elasticsearch: Store logs
- Logstash: Process logs
- Kibana: Visualize logs

### Alerting

**Alert Manager Configuration:**
```yaml
# alertmanager.yml
route:
  group_by: ['alertname']
  receiver: 'email'
  
receivers:
  - name: 'email'
    email_configs:
      - to: 'ops@yourcompany.com'
        from: 'alerts@yourcompany.com'
```

**Alert Rules:**
```yaml
# alerts.yml
groups:
  - name: rag_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
      
      - alert: SlowResponses
        expr: http_request_duration_seconds{quantile="0.95"} > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API responses are slow"
      
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
```

## Backup & Recovery

### Automated Backups

**Backup Script** (`scripts/backup.sh`):
```bash
#!/bin/bash
set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
docker-compose exec -T postgres pg_dump -U postgres research_papers | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# OpenSearch snapshot
curl -X PUT "localhost:9200/_snapshot/backup/snapshot_$DATE?wait_for_completion=true"

# Compress and upload to S3
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" "$BACKUP_DIR/postgres_$DATE.sql.gz"
aws s3 cp "$BACKUP_DIR/backup_$DATE.tar.gz" s3://your-backup-bucket/

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Cron Job:**
```bash
# Daily backups at 2 AM
0 2 * * * /opt/research-paper-curator/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### Disaster Recovery Plan

1. **Document recovery procedures**
2. **Test recovery regularly** (monthly)
3. **Store backups off-site**
4. **Have rollback plan**
5. **Maintain runbook**

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose logs -f <service-name>

# Check container status
docker ps -a

# Restart service
docker-compose restart <service-name>
```

#### Database Connection Issues
```bash
# Test connection
docker-compose exec postgres psql -U postgres -d research_papers

# Check connection pool
docker-compose exec api python -c "from src.database.connection import check_db_connection; print(check_db_connection())"
```

#### High Memory Usage
```bash
# Check resource usage
docker stats

# Restart heavy services
docker-compose restart opensearch ollama
```

#### Slow Queries
```bash
# Enable slow query log (PostgreSQL)
docker-compose exec postgres psql -U postgres -c "ALTER SYSTEM SET log_min_duration_statement = 1000;"

# Analyze query performance
EXPLAIN ANALYZE SELECT ...;
```

### Health Check Script
```bash
#!/bin/bash
# scripts/health_check.sh

echo "Checking system health..."

# API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API: Healthy"
else
    echo "✗ API: Down"
    exit 1
fi

# PostgreSQL
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✓ PostgreSQL: Healthy"
else
    echo "✗ PostgreSQL: Down"
    exit 1
fi

# Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis: Healthy"
else
    echo "✗ Redis: Down"
    exit 1
fi

# OpenSearch
if curl -f http://localhost:9200/_cluster/health > /dev/null 2>&1; then
    echo "✓ OpenSearch: Healthy"
else
    echo "✗ OpenSearch: Down"
    exit 1
fi

echo "All services healthy!"
```

## Scaling Strategies

### Vertical Scaling
- Upgrade server resources
- Increase container limits
- Tune database parameters

### Horizontal Scaling
```bash
# Scale API instances
docker-compose up -d --scale api=5

# Load balancer configuration
# Add to nginx upstream block
```

### Database Scaling
- Read replicas for queries
- Connection pooling
- Query optimization
- Partitioning

## Security Checklist

- [ ] Change all default passwords
- [ ] Enable SSL/TLS
- [ ] Configure firewall
- [ ] Enable database encryption
- [ ] Implement rate limiting
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Review security groups
- [ ] Enable audit logging
- [ ] Update dependencies regularly

## Post-Deployment

1. **Run health checks**
2. **Test all endpoints**
3. **Monitor logs for errors**
4. **Set up alerts**
5. **Document any issues**
6. **Create rollback plan**
7. **Schedule maintenance windows**

---

**Deployment Support**: devops@yourcompany.com
**Emergency Contact**: +1-XXX-XXX-XXXX
**Last Updated**: 2025-10-14