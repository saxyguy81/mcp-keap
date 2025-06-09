# Production Deployment Guide

## Overview

This guide covers deploying the Keap MCP service-oriented architecture in production environments with optimal performance, security, and monitoring.

## Prerequisites

### System Requirements
- **Python**: 3.11+ (recommended: 3.11.6)
- **Memory**: Minimum 512MB, Recommended 2GB+
- **Storage**: 1GB+ for application and cache
- **CPU**: 2+ cores recommended for optimal performance
- **Network**: Stable internet connection for Keap API access

### Dependencies
```bash
# Core dependencies
httpx>=0.25.0          # HTTP/2 support and async requests
pydantic>=2.0.0        # Data validation and serialization
asyncio                # Async runtime (built-in)
sqlite3                # Caching backend (built-in)

# Optional production dependencies
uvloop>=0.17.0         # High-performance event loop
gunicorn>=21.0.0       # WSGI server for production
prometheus-client      # Metrics export
structlog              # Structured logging
```

## Environment Configuration

### Core Configuration File
Create `.env` file in project root:

```bash
# ==== KEAP API CONFIGURATION ====
KEAP_API_KEY=your_production_api_key_here
KEAP_API_BASE_URL=https://api.infusionsoft.com/crm/rest/v1

# ==== OPTIMIZATION SETTINGS ====
# Enable all optimizations for production
ENABLE_OPTIMIZATIONS=true
ENABLE_PERFORMANCE_MONITORING=true

# Phase 1 Optimizations
MAX_CONCURRENT_TAG_QUERIES=5
FILTER_SELECTIVITY_LEARNING=true
ADAPTIVE_BATCH_SIZING=true
BATCH_SIZE_MIN=10
BATCH_SIZE_MAX=500
BATCH_SIZE_DEFAULT=100

# Phase 2 Optimizations
ENABLE_API_PARAMETER_OPTIMIZATION=true
SERVER_SIDE_FILTERING_ENABLED=true

# ==== CONNECTION POOL SETTINGS ====
MAX_CONNECTIONS=50
MAX_CONNECTIONS_PER_HOST=10
ENABLE_HTTP2=true
CONNECTION_TIMEOUT=15.0
KEEP_ALIVE_TIMEOUT=60.0
MAX_IDLE_TIME=300.0

# ==== PERFORMANCE MONITORING ====
METRIC_COLLECTION_INTERVAL=10.0
PERFORMANCE_HISTORY_HOURS=48
ALERT_ERROR_RATE_THRESHOLD=0.05
ALERT_RESPONSE_TIME_THRESHOLD_MS=3000
ALERT_CACHE_HIT_RATIO_THRESHOLD=0.7

# ==== CACHE CONFIGURATION ====
CACHE_DB_PATH=/app/data/keap_cache.db
CACHE_MAX_ENTRIES=50000
CACHE_MAX_MEMORY_MB=500
CACHE_DEFAULT_TTL=3600

# ==== LOGGING CONFIGURATION ====
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/app/logs/keap_mcp.log
LOG_ROTATION_SIZE=100MB
LOG_RETENTION_DAYS=30

# ==== SECURITY SETTINGS ====
RATE_LIMIT_PER_MINUTE=1000
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=2.0

# ==== HEALTH CHECK SETTINGS ====
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=5.0
HEALTH_CHECK_ENDPOINT=/health
```

### Environment-Specific Configurations

#### Development Environment
```bash
# .env.development
LOG_LEVEL=DEBUG
ENABLE_PERFORMANCE_MONITORING=true
MAX_CONNECTIONS=10
METRIC_COLLECTION_INTERVAL=1.0
CACHE_MAX_ENTRIES=1000
```

#### Staging Environment
```bash
# .env.staging
LOG_LEVEL=INFO
ENABLE_OPTIMIZATIONS=true
MAX_CONNECTIONS=25
PERFORMANCE_HISTORY_HOURS=24
CACHE_MAX_ENTRIES=25000
```

#### Production Environment
```bash
# .env.production
LOG_LEVEL=WARNING
ENABLE_OPTIMIZATIONS=true
ENABLE_PERFORMANCE_MONITORING=true
MAX_CONNECTIONS=50
PERFORMANCE_HISTORY_HOURS=72
CACHE_MAX_ENTRIES=100000
```

## Docker Deployment

### Production Dockerfile
```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create app user for security
RUN groupadd -r app && useradd -r -g app app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Create directories
RUN mkdir -p /app/data /app/logs && \
    chown -R app:app /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=app:app . .

# Install additional production dependencies
RUN pip install --no-cache-dir \
    uvloop>=0.17.0 \
    gunicorn>=21.0.0 \
    prometheus-client \
    structlog

# Switch to app user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import asyncio; from src.health import health_check; asyncio.run(health_check())"

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--access-logfile", "-", "--error-logfile", "-", "src.main:app"]
```

### Docker Compose for Production
```yaml
version: '3.8'

services:
  keap-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=production
    env_file:
      - .env.production
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - keap_network

  # Optional: Redis for distributed caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - keap_network

  # Optional: Prometheus for metrics
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - keap_network

  # Optional: Grafana for visualization
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    networks:
      - keap_network

volumes:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  keap_network:
    driver: bridge
```

## Kubernetes Deployment

### Deployment Configuration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: keap-mcp
  labels:
    app: keap-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: keap-mcp
  template:
    metadata:
      labels:
        app: keap-mcp
    spec:
      containers:
      - name: keap-mcp
        image: keap-mcp:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENV
          value: "production"
        envFrom:
        - secretRef:
            name: keap-mcp-secrets
        - configMapRef:
            name: keap-mcp-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
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
        volumeMounts:
        - name: data-storage
          mountPath: /app/data
        - name: log-storage
          mountPath: /app/logs
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: keap-mcp-data
      - name: log-storage
        persistentVolumeClaim:
          claimName: keap-mcp-logs
```

### Service Configuration
```yaml
apiVersion: v1
kind: Service
metadata:
  name: keap-mcp-service
spec:
  selector:
    app: keap-mcp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: keap-mcp-config
data:
  ENABLE_OPTIMIZATIONS: "true"
  MAX_CONNECTIONS: "50"
  LOG_LEVEL: "INFO"
  CACHE_MAX_ENTRIES: "50000"
```

### Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: keap-mcp-secrets
type: Opaque
data:
  KEAP_API_KEY: <base64-encoded-api-key>
```

## Monitoring and Logging

### Prometheus Metrics Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'keap-mcp'
    static_configs:
      - targets: ['keap-mcp:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### Log Aggregation with Fluentd
```yaml
# logging/fluentd.conf
<source>
  @type tail
  path /app/logs/*.log
  pos_file /var/log/fluentd/keap-mcp.log.pos
  tag keap.mcp
  format json
</source>

<match keap.mcp>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name keap-mcp
  type_name _doc
</match>
```

### Grafana Dashboard Configuration
```json
{
  "dashboard": {
    "title": "Keap MCP Performance",
    "panels": [
      {
        "title": "Query Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, keap_mcp_query_duration_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(keap_mcp_errors_total[5m])"
          }
        ]
      },
      {
        "title": "Cache Hit Ratio",
        "type": "gauge",
        "targets": [
          {
            "expr": "keap_mcp_cache_hits_total / (keap_mcp_cache_hits_total + keap_mcp_cache_misses_total)"
          }
        ]
      }
    ]
  }
}
```

## Performance Tuning

### Production Optimizations

#### Python Runtime
```bash
# Use uvloop for better async performance
pip install uvloop

# Enable in main.py
import uvloop
uvloop.install()
```

#### Connection Pool Tuning
```python
# For high-throughput environments
MAX_CONNECTIONS = 100
MAX_CONNECTIONS_PER_HOST = 20
KEEP_ALIVE_TIMEOUT = 120.0

# For memory-constrained environments
MAX_CONNECTIONS = 20
MAX_CONNECTIONS_PER_HOST = 5
KEEP_ALIVE_TIMEOUT = 30.0
```

#### Cache Optimization
```python
# For high-memory environments
CACHE_MAX_ENTRIES = 100000
CACHE_MAX_MEMORY_MB = 1000

# For SSD storage
CACHE_DB_PATH = "/fast-ssd/keap_cache.db"
```

### Load Testing
```bash
# Install load testing tools
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:8000
```

## Security Hardening

### API Security
- Store API keys in secure secret management systems
- Rotate API keys regularly
- Monitor API usage for anomalies
- Implement rate limiting and request throttling

### Container Security
```dockerfile
# Security hardening in Dockerfile
RUN apt-get update && apt-get upgrade -y
RUN rm -rf /var/lib/apt/lists/*
USER app  # Never run as root
```

### Network Security
- Use HTTPS for all external communications
- Implement proper firewall rules
- Use VPC/private networks in cloud deployments
- Regular security scanning and updates

## Backup and Recovery

### Data Backup
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/keap-mcp"

# Backup cache database
cp /app/data/keap_cache.db $BACKUP_DIR/cache_$DATE.db

# Backup configuration
cp /app/.env.production $BACKUP_DIR/config_$DATE.env

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz /app/logs/
```

### Disaster Recovery
1. **Database Recovery**: Restore from most recent cache backup
2. **Configuration Recovery**: Restore environment configuration
3. **Service Recovery**: Redeploy with validated configuration
4. **Health Verification**: Run comprehensive health checks

## Operational Procedures

### Deployment Checklist
- [ ] Environment configuration validated
- [ ] API keys and secrets properly configured
- [ ] Database migrations completed
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Backup procedures tested
- [ ] Performance benchmarks validated
- [ ] Security scan completed

### Maintenance Procedures
- **Weekly**: Review performance metrics and optimization effectiveness
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Performance tuning and capacity planning
- **Annually**: Architecture review and optimization strategy assessment

### Troubleshooting
1. **High Response Times**: Check connection pool utilization and API optimization effectiveness
2. **Memory Issues**: Monitor cache size and adjust limits
3. **API Errors**: Verify API key validity and rate limiting
4. **Connection Issues**: Check network connectivity and firewall rules

This deployment guide ensures a robust, secure, and performant production deployment of the Keap MCP service-oriented architecture.