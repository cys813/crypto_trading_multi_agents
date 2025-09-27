# Long Analyst Agent Deployment Guide

## Overview

This comprehensive deployment guide provides instructions for deploying the Long Analyst Agent in various environments, from development to production. The guide covers containerization, orchestration, monitoring, and security best practices.

## System Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **Memory**: 8 GB RAM
- **Storage**: 50 GB SSD
- **Network**: 100 Mbps
- **OS**: Ubuntu 20.04+ or equivalent

### Recommended Requirements (Production)
- **CPU**: 16+ cores
- **Memory**: 32 GB RAM
- **Storage**: 200 GB SSD
- **Network**: 1 Gbps
- **OS**: Ubuntu 22.04 LTS

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Load Balancer                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   API       │  │   Web       │  │   Admin    │          │
│  │ Gateway     │  │ Socket      │  │   Panel     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
├─────────────────────────────────────────────────────────────────┤
│                    Long Analyst Agent Cluster                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Instance  │  │   Instance  │  │   Instance  │          │
│  │     1       │  │     2       │  │     3       │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
├─────────────────────────────────────────────────────────────────┤
│                      Data Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ PostgreSQL  │  │    Redis    │  │ InfluxDB    │          │
│  │   (Primary) │  │   (Cache)   │  │ (Time Series)│          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
├─────────────────────────────────────────────────────────────────┤
│                    Monitoring & Logging                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Prometheus  │  │   Grafana   │  │   ELK       │          │
│  │   (Metrics) │  │ (Dashboard) │  │  (Logging)  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install kubectl (for Kubernetes deployment)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm (for Kubernetes package management)
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm
```

### Clone Repository
```bash
git clone https://github.com/your-org/long-analyst-agent.git
cd long-analyst-agent
```

### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### Environment Variables
```bash
# Application Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG_MODE=false

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0
API_WORKERS=4
MAX_REQUEST_SIZE=100MB

# Database Configuration
DATABASE_URL=postgresql://user:password@postgres:5432/longanalyst
REDIS_URL=redis://redis:6379/0
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-influxdb-token
INFLUXDB_ORG=your-org
INFLUXDB_BUCKET=longanalyst

# LLM Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
AZURE_OPENAI_KEY=your-azure-key (optional)
AZURE_OPENAI_ENDPOINT=your-azure-endpoint (optional)

# Security Configuration
JWT_SECRET=your-jwt-secret-key
API_RATE_LIMIT=1000
CORS_ORIGINS=https://yourdomain.com

# Performance Configuration
MAX_CONCURRENT_REQUESTS=1000
CACHE_TTL=300
ANALYSIS_TIMEOUT=5000

# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=9090
ENABLE_TRACING=true
JAEGER_ENDPOINT=http://jaeger:14268/api/traces
```

### Development Deployment
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f

# Stop development environment
docker-compose -f docker-compose.dev.yml down
```

## Production Deployment

### 1. Docker Compose Deployment

#### docker-compose.yml
```yaml
version: '3.8'

services:
  # Long Analyst Agent
  long-analyst:
    image: long-analyst:latest
    restart: unless-stopped
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - INFLUXDB_URL=${INFLUXDB_URL}
      - INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
      - INFLUXDB_ORG=${INFLUXDB_ORG}
      - INFLUXDB_BUCKET=${INFLUXDB_BUCKET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ENVIRONMENT=production
    ports:
      - "8000:8000"
      - "9090:9090"
    depends_on:
      - postgres
      - redis
      - influxdb
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # PostgreSQL Database
  postgres:
    image: postgres:15
    restart: unless-stopped
    environment:
      POSTGRES_DB: longanalyst
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G

  # Redis Cache
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G

  # InfluxDB Time Series Database
  influxdb:
    image: influxdb:2.7
    restart: unless-stopped
    environment:
      DOCKER_INFLUXDB_INIT_MODE=setup
      DOCKER_INFLUXDB_INIT_USERNAME=admin
      DOCKER_INFLUXDB_INIT_PASSWORD=${INFLUXDB_PASSWORD}
      DOCKER_INFLUXDB_INIT_ORG=${INFLUXDB_ORG}
      DOCKER_INFLUXDB_INIT_BUCKET=${INFLUXDB_BUCKET}
      DOCKER_INFLUXDB_INIT_RETENTION=30d
      DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=${INFLUXDB_TOKEN}
    volumes:
      - influxdb_data:/var/lib/influxdb2
    ports:
      - "8086:8086"

  # Prometheus Metrics
  prometheus:
    image: prom/prometheus:latest
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9091:9090"

  # Grafana Dashboard
  grafana:
    image: grafana/grafana:latest
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3000:3000"
    depends_on:
      - prometheus

volumes:
  postgres_data:
  redis_data:
  influxdb_data:
  prometheus_data:
  grafana_data:
```

#### Deployment Commands
```bash
# Build and start services
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f long-analyst

# Scale services
docker-compose up -d --scale long-analyst=3

# Stop services
docker-compose down
```

### 2. Kubernetes Deployment

#### Namespace Creation
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: long-analyst
  labels:
    name: long-analyst
```

#### ConfigMap
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: long-analyst-config
  namespace: long-analyst
data:
  LOG_LEVEL: "INFO"
  DEBUG_MODE: "false"
  ENVIRONMENT: "production"
  MAX_CONCURRENT_REQUESTS: "1000"
  CACHE_TTL: "300"
  ANALYSIS_TIMEOUT: "5000"
  ENABLE_METRICS: "true"
  ENABLE_TRACING: "true"
```

#### Secret
```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: long-analyst-secrets
  namespace: long-analyst
type: Opaque
data:
  # Base64 encoded values
  database-url: <base64-encoded-database-url>
  redis-url: <base64-encoded-redis-url>
  influxdb-url: <base64-encoded-influxdb-url>
  influxdb-token: <base64-encoded-influxdb-token>
  openai-api-key: <base64-encoded-openai-key>
  jwt-secret: <base64-encoded-jwt-secret>
```

#### Deployment
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: long-analyst
  namespace: long-analyst
  labels:
    app: long-analyst
spec:
  replicas: 3
  selector:
    matchLabels:
      app: long-analyst
  template:
    metadata:
      labels:
        app: long-analyst
    spec:
      containers:
      - name: long-analyst
        image: long-analyst:latest
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 9090
          name: metrics
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: long-analyst-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: long-analyst-secrets
              key: redis-url
        - name: INFLUXDB_URL
          valueFrom:
            secretKeyRef:
              name: long-analyst-secrets
              key: influxdb-url
        - name: INFLUXDB_TOKEN
          valueFrom:
            secretKeyRef:
              name: long-analyst-secrets
              key: influxdb-token
        - name: INFLUXDB_ORG
          valueFrom:
            configMapKeyRef:
              name: long-analyst-config
              key: influxdb-org
        - name: INFLUXDB_BUCKET
          valueFrom:
            configMapKeyRef:
              name: long-analyst-config
              key: influxdb-bucket
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: long-analyst-secrets
              key: openai-api-key
        envFrom:
        - configMapRef:
            name: long-analyst-config
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: long-analyst-service
  namespace: long-analyst
spec:
  selector:
    app: long-analyst
  ports:
  - name: http
    port: 80
    targetPort: 8000
  - name: metrics
    port: 9090
    targetPort: 9090
  type: ClusterIP
```

#### Ingress
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: long-analyst-ingress
  namespace: long-analyst
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.longanalyst.com
    secretName: long-analyst-tls
  rules:
  - host: api.longanalyst.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: long-analyst-service
            port:
              number: 80
```

#### Horizontal Pod Autoscaler
```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: long-analyst-hpa
  namespace: long-analyst
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: long-analyst
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

#### Deployment Commands
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n long-analyst
kubectl get services -n long-analyst
kubectl get hpa -n long-analyst

# View logs
kubectl logs -f deployment/long-analyst -n long-analyst

# Scale deployment
kubectl scale deployment long-analyst --replicas=5 -n long-analyst
```

### 3. Helm Chart Deployment

#### Create Helm Chart
```bash
# Create chart structure
helm create long-analyst-chart
cd long-analyst-chart
```

#### values.yaml
```yaml
# Default values for long-analyst-chart
replicaCount: 3

image:
  repository: long-analyst
  pullPolicy: IfNotPresent
  tag: "latest"

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: api.longanalyst.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: long-analyst-tls
      hosts:
        - api.longanalyst.com

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 500m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

config:
  logLevel: "INFO"
  debugMode: "false"
  environment: "production"
  maxConcurrentRequests: "1000"
  cacheTtl: "300"
  analysisTimeout: "5000"
  enableMetrics: "true"
  enableTracing: "true"

secrets:
  databaseUrl: ""
  redisUrl: ""
  influxdbUrl: ""
  influxdbToken: ""
  openaiApiKey: ""
  jwtSecret: ""

postgresql:
  enabled: true
  auth:
    database: longanalyst
    username: postgres
    password: postgres
  primary:
    persistence:
      enabled: true
      size: 20Gi

redis:
  enabled: true
  auth:
    password: redis
  master:
    persistence:
      enabled: true
      size: 10Gi

influxdb:
  enabled: true
  auth:
    admin:
      token: influxdb-token
      org: longanalyst
      bucket: longanalyst
  persistence:
    enabled: true
    size: 20Gi

monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true
    adminPassword: admin
```

#### Helm Deployment Commands
```bash
# Install dependencies
helm dependency update

# Install chart
helm install long-analyst ./long-analyst-chart -n long-analyst --create-namespace

# Upgrade chart
helm upgrade long-analyst ./long-analyst-chart -n long-analyst

# Uninstall chart
helm uninstall long-analyst -n long-analyst
```

## Monitoring and Observability

### 1. Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'long-analyst'
    static_configs:
      - targets: ['long-analyst:9090']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'influxdb'
    static_configs:
      - targets: ['influxdb:8086']
```

### 2. Grafana Dashboards

#### Import Dashboard
```json
{
  "dashboard": {
    "id": null,
    "title": "Long Analyst Agent Dashboard",
    "tags": ["long-analyst"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "API Requests",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      }
    ]
  }
}
```

### 3. Logging with ELK Stack

#### Logstash Configuration
```ruby
# logstash/pipeline.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "long-analyst" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}" }
    }
    date {
      match => [ "timestamp", "ISO8601" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "long-analyst-%{+YYYY.MM.dd}"
  }
}
```

## Security and Best Practices

### 1. Network Security

#### Network Policies
```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: long-analyst-network-policy
  namespace: long-analyst
spec:
  podSelector:
    matchLabels:
      app: long-analyst
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 6379  # Redis
    - protocol: TCP
      port: 8086  # InfluxDB
```

### 2. Resource Security

#### Pod Security Context
```yaml
# security-context.yaml
apiVersion: v1
kind: Pod
metadata:
  name: long-analyst-secure
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
  containers:
  - name: long-analyst
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      capabilities:
        drop:
        - ALL
```

### 3. Secrets Management

#### Using Sealed Secrets
```bash
# Install Sealed Secrets
helm install sealed-secrets sealed-secrets/sealed-secrets

# Create sealed secret
kubeseal --format=yaml --cert=cert.pem < secret.yaml > sealed-secret.yaml
```

### 4. TLS Configuration

#### Certificate Management
```yaml
# cert-manager/issuer.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@longanalyst.com
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
    - http01:
        ingress:
          class: nginx
```

## Performance Optimization

### 1. Database Optimization

#### PostgreSQL Tuning
```sql
-- PostgreSQL optimization queries
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
```

#### Redis Configuration
```bash
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
tcp-keepalive 300
timeout 0
```

### 2. Application Optimization

#### Gunicorn Configuration
```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
keepalive = 2
timeout = 30
graceful_timeout = 30
```

### 3. Caching Strategy

#### Multi-level Caching
```python
# cache_manager.py
import redis
import json
from functools import wraps
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        self.local_cache = {}

    def cached(self, ttl=300):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

                # Check local cache first
                if cache_key in self.local_cache:
                    cached_data, timestamp = self.local_cache[cache_key]
                    if datetime.now() - timestamp < timedelta(seconds=ttl):
                        return cached_data

                # Check Redis cache
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    self.local_cache[cache_key] = (data, datetime.now())
                    return data

                # Execute function and cache result
                result = await func(*args, **kwargs)
                self.redis_client.setex(cache_key, ttl, json.dumps(result))
                self.local_cache[cache_key] = (result, datetime.now())

                return result
            return wrapper
        return decorator
```

## Backup and Recovery

### 1. Database Backup

#### PostgreSQL Backup Script
```bash
#!/bin/bash
# backup-postgres.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
DB_NAME="longanalyst"
DB_USER="postgres"
DB_HOST="postgres"
DB_PORT="5432"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/postgres_backup_$DATE.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "postgres_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: postgres_backup_$DATE.sql.gz"
```

#### InfluxDB Backup
```bash
#!/bin/bash
# backup-influxdb.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/influxdb"
INFLUXDB_HOST="influxdb"
INFLUXDB_PORT="8086"
INFLUXDB_ORG="longanalyst"
INFLUXDB_BUCKET="longanalyst"
INFLUXDB_TOKEN="your-token"

mkdir -p $BACKUP_DIR

# Create backup
influxd backup --host $INFLUXDB_HOST:$INFLUXDB_PORT \
  --org $INFLUXDB_ORG \
  --token $INFLUXDB_TOKEN \
  --bucket $INFLUXDB_BUCKET \
  $BACKUP_DIR/influxdb_backup_$DATE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "influxdb_backup_*" -mtime +7 -delete

echo "Backup completed: influxdb_backup_$DATE"
```

### 2. Disaster Recovery

#### Restore Script
```bash
#!/bin/bash
# restore.sh

BACKUP_DATE=$1
BACKUP_DIR="/backups"

# Restore PostgreSQL
if [ -f "$BACKUP_DIR/postgres/postgres_backup_$BACKUP_DATE.sql.gz" ]; then
    gunzip -c $BACKUP_DIR/postgres/postgres_backup_$BACKUP_DATE.sql.gz | \
    psql -h postgres -U postgres -d longanalyst
    echo "PostgreSQL restored from $BACKUP_DATE"
fi

# Restore InfluxDB
if [ -d "$BACKUP_DIR/influxdb/influxdb_backup_$BACKUP_DATE" ]; then
    influxd restore --host influxdb:8086 \
      --org longanalyst \
      --token your-token \
      $BACKUP_DIR/influxdb/influxdb_backup_$BACKUP_DATE
    echo "InfluxDB restored from $BACKUP_DATE"
fi
```

## Testing and Quality Assurance

### 1. Unit Testing

#### Test Configuration
```python
# tests/conftest.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.long_analyst.main import app
from src.long_analyst.database import get_db
from src.long_analyst.models import Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    return TestClient(app)
```

### 2. Integration Testing

#### Integration Tests
```python
# tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from src.long_analyst.main import app

client = TestClient(app)

def test_analysis_endpoint():
    response = client.post(
        "/analyze/symbol",
        json={
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "include_technical": True,
            "include_fundamental": True,
            "include_sentiment": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "signals" in data["data"]

def test_performance_endpoint():
    response = client.get("/analytics/performance?timeframe=24h")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "metrics" in data["data"]
```

### 3. Load Testing

#### Locust Configuration
```python
# locustfile.py
from locust import HttpUser, task, between
import json

class LongAnalystUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        self.headers = {"Authorization": "Bearer your-api-key"}

    @task
    def analyze_symbol(self):
        payload = {
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "include_technical": True,
            "include_fundamental": True,
            "include_sentiment": True
        }
        self.client.post(
            "/analyze/symbol",
            json=payload,
            headers=self.headers
        )

    @task(3)
    def get_signals(self):
        self.client.get("/signals", headers=self.headers)

    @task(2)
    def get_performance(self):
        self.client.get("/analytics/performance", headers=self.headers)
```

#### Run Load Test
```bash
# Start Locust
locust -f locustfile.py --host=http://localhost:8000

# Headless mode
locust -f locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 60s
```

## Troubleshooting

### Common Issues

#### 1. High Memory Usage
```bash
# Check memory usage
docker stats long-analyst

# Restart container
docker-compose restart long-analyst

# Check logs for memory leaks
docker-compose logs --tail=100 long-analyst
```

#### 2. Database Connection Issues
```bash
# Check database connectivity
docker-compose exec postgres psql -U postgres -d longanalyst -c "SELECT 1"

# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

#### 3. API Performance Issues
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/health"

# Check database query performance
docker-compose exec postgres psql -U postgres -d longanalyst -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Clear cache
docker-compose exec redis redis-cli FLUSHDB
```

### Log Analysis

#### Filter Logs
```bash
# Error logs
docker-compose logs long-analyst | grep ERROR

# Performance logs
docker-compose logs long-analyst | grep "processing_time"

# API request logs
docker-compose logs long-analyst | grep "request"
```

#### Debug Mode
```bash
# Enable debug mode
export DEBUG_MODE=true
docker-compose up -d --build long-analyst

# View debug logs
docker-compose logs --tail=100 -f long-analyst
```

## Conclusion

This comprehensive deployment guide provides all the necessary information to deploy the Long Analyst Agent in various environments. The guide covers:

1. **Architecture Overview**: High-level system design and components
2. **Quick Start**: Fast setup for development and testing
3. **Production Deployment**: Docker Compose and Kubernetes configurations
4. **Monitoring and Observability**: Comprehensive monitoring setup
5. **Security**: Network, resource, and secrets security
6. **Performance Optimization**: Database, application, and caching optimization
7. **Backup and Recovery**: Disaster recovery procedures
8. **Testing and Quality Assurance**: Testing strategies and tools
9. **Troubleshooting**: Common issues and solutions

The deployment is designed to be scalable, secure, and maintainable, with comprehensive monitoring and logging capabilities. The guide provides multiple deployment options to suit different organizational needs and infrastructure requirements.