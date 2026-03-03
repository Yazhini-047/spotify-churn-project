# Role 3 — Deployment & Operations Guide
## Complete Backend Deployment for Spotify Churn Prediction

**Version:** 1.0  
**Date:** 2026-02-26  
**Author:** Role 3 Backend Developer

---

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Local Development Setup](#local-development-setup)
4. [Docker & Container Deployment](#docker--container-deployment)
5. [Production Deployment](#production-deployment)
6. [Database Management](#database-management)
7. [API Integration](#api-integration)
8. [Monitoring & Logs](#monitoring--logs)
9. [Troubleshooting](#troubleshooting)
10. [CI/CD Pipeline](#cicd-pipeline)

---

## Overview

This guide covers the complete deployment strategy for the Spotify Churn Prediction backend system built in Role 3. The backend provides:

### **Key Services**
- **REST API Endpoints** for predictions, explanations, playbooks, and chatbot
- **Database Layer** with PostgreSQL for logging and persistence
- **Cache Layer** with Redis for session management
- **Async Processing** for long-running tasks
- **Monitoring & Logging** for observability

### **Technology Stack**
```
├── FastAPI 0.104+ (Web Framework)
├── PostgreSQL 15 (Database)
├── Redis 7 (Cache)
├── Docker & Docker Compose (Containerization)
├── Uvicorn (ASGI Server)
├── Pytest (Testing)
└── SQLAlchemy 2.0 (ORM)
```

---

## Architecture

### **System Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                     EXTERNAL CLIENTS                         │
│              (Web App, Mobile App, Webhook)                  │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API
                     ▼
        ┌──────────────────────────┐
        │   FastAPI Backend        │
        │  (8 API Endpoints)       │
        │  - /predict              │
        │  - /explain              │
        │  - /playbook/*           │
        │  - /chat                 │
        └──────┬───────────┬───────┘
               │           │
         ┌─────▼──┐   ┌────▼──────┐
         │PostgreSQL    Redis Cache │
         │ (Logs DB) │   (Sessions)  │
         └──────────┘   └────────────┘
```

### **Data Flow**

```
User Request
    │
    ▼
FastAPI Route Handler
    │
    ├─► Load/Cache Model
    ├─► Role 1: Generate Prediction
    ├─► Role 2: Generate Explanation
    ├─► Role 2: Recommend Playbooks
    ├─► Chatbot Flows: Process Intent
    │
    ▼
Database Layer
    │
    ├─► Log Prediction
    ├─► Log Chat Message
    ├─► Log Playbook Execution
    │
    ▼
Response to Client (JSON / Webhook)
```

---

## Local Development Setup

### **Prerequisites**

```bash
# System Requirements
- Python 3.11+
- PostgreSQL 14+ (or SQLite for dev)
- Redis 7+ (optional for dev)
- Docker & Docker Compose (for containerized dev)
- Git
```

### **Step 1: Clone & Setup**

```bash
# Clone repository
git clone <repo-url> spotify_churn_prediction
cd spotify_churn_prediction

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **Step 2: Configure Environment**

Create `.env` file:

```bash
# .env (Development)
ENVIRONMENT=development
DATABASE_URL=sqlite:///./chatbot.db
REDIS_URL=redis://localhost:6379
LOG_LEVEL=DEBUG
WORKERS=1

# API Config
API_TITLE="Spotify Churn Prediction"
API_VERSION=1.0.0

# Model Paths
MODEL_PATH=./model.pkl
EXPLAINER_PATH=./explainer.pkl
PLAYBOOK_PATH=./02_PLAYBOOK_RULESET.json
```

### **Step 3: Initialize Database**

```bash
# Using SQLAlchemy
python -c "from database_layer import db_manager; db_manager.create_tables()"

# Or using Alembic (for migrations)
alembic upgrade head
```

### **Step 4: Load Models**

```bash
# Copy model files to project root
cp /path/to/model.pkl .
cp /path/to/explainer.pkl .

# Test model loading
python -c "import joblib; model = joblib.load('model.pkl'); print(model)"
```

### **Step 5: Run Development Server**

```bash
# Start with hot reload
uvicorn backend_app:app --reload --host 0.0.0.0 --port 8000

# Server available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

---

## Docker & Container Deployment

### **Using Docker Compose (Recommended for Dev/Test)**

#### **Step 1: Build Images**

```bash
# Build all services
docker-compose build

# Or build specific service
docker-compose build backend
```

#### **Step 2: Start Services**

```bash
# Start all services
docker-compose up -d

# Monitor logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

#### **Step 3: Access Services**

```bash
# Backend API
curl http://localhost:8000/health

# Database Admin (Adminer)
http://localhost:8080

# PostgreSQL
Host: localhost
Port: 5432
User: postgres
Password: spotify123
DB: spotify_churn
```

### **Docker Compose Environment Variables**

Edit `docker-compose.yml` to configure:

```yaml
environment:
  DATABASE_URL: postgresql://postgres:spotify123@postgres:5432/spotify_churn
  ENVIRONMENT: production
  LOG_LEVEL: info
  WORKERS: 4
```

### **View Container Logs**

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Follow last 100 lines
docker-compose logs --tail=100 backend
```

### **Scale Services**

```bash
# Run multiple backend instances (with load balancer)
docker-compose up -d --scale backend=3
```

---

## Production Deployment

### **Option 1: AWS ECS (Elastic Container Service)**

#### **Prepare**

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name spotify-churn-backend

# 2. Build and push image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag spotify_churn_backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/spotify-churn-backend:latest

docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/spotify-churn-backend:latest
```

#### **Deploy**

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name spotify-churn

# Create task definition (from ecs-task-definition.json)
aws ecs register-task-definition \
  --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster spotify-churn \
  --service-name spotify-churn-api \
  --task-definition spotify-churn-backend:latest \
  --desired-count 3 \
  --load-balancers targetGroupArn=<target-group-arn>,containerName=backend,containerPort=8000
```

### **Option 2: Kubernetes (K8s)**

#### **Create Deployment**

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spotify-churn-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: spotify-churn
  template:
    metadata:
      labels:
        app: spotify-churn
    spec:
      containers:
      - name: backend
        image: spotify_churn_backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: database-url
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
```

#### **Deploy**

```bash
# Create namespace
kubectl create namespace spotify

# Create secrets
kubectl create secret generic db-credentials \
  --from-literal=database-url=postgresql://... \
  -n spotify

# Deploy
kubectl apply -f kubernetes/ -n spotify

# Monitor
kubectl get pods -n spotify
kubectl logs -f deployment/spotify-churn-backend -n spotify
```

### **Option 3: Heroku (Simple Deployment)**

```bash
# Install Heroku CLI
curl https://cli.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create spotify-churn-backend

# Add PostgreSQL
heroku addons:create heroku-postgresql:standard-0 -a spotify-churn-backend

# Set environment
heroku config:set ENVIRONMENT=production -a spotify-churn-backend

# Deploy
git push heroku main

# View logs
heroku logs --tail -a spotify-churn-backend
```

---

## Database Management

### **PostgreSQL Setup**

#### **Create Database**

```bash
# Connect to PostgreSQL
psql -U postgres -h localhost

# Create database
CREATE DATABASE spotify_churn;

# Create user
CREATE USER spotify_user WITH PASSWORD 'secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE spotify_churn TO spotify_user;
```

#### **Initialize Schema**

```bash
# Using Alembic (recommended)
alembic upgrade head

# Or manually create tables
python -c "from database_layer import db_manager; db_manager.create_tables()"
```

### **Database Backup & Restore**

```bash
# Backup
pg_dump -U postgres -h localhost spotify_churn > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
psql -U postgres -h localhost spotify_churn < backup_20260226_120000.sql
```

### **Database Monitoring**

```sql
-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname != 'pg_catalog' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check active connections
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;

-- Check query performance
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;
```

---

## API Integration

### **Authentication (Optional)**

Add JWT authentication to `backend_app.py`:

```python
from fastapi import Depends
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id

@app.post("/predict")
async def predict(request: PredictionRequest, user_id: str = Depends(verify_token)):
    # Protected endpoint
    ...
```

### **Rate Limiting**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/predict")
@limiter.limit("100/minute")
async def predict(request: Request, ...):
    ...
```

### **CORS Configuration**

Update `backend_app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    max_age=3600,
)
```

---

## Monitoring & Logs

### **Application Logging**

Logs are written to `backend.log` with format:

```
2026-02-26 12:34:56,789 - backend_app - INFO - Prediction for user_001: 75.34%
```

### **Setup ELK Stack (Elasticsearch, Logstash, Kibana)**

```yaml
# docker-compose-monitoring.yml
version: '3.9'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"
  
  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
  
  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
```

### **Prometheus Metrics**

```python
from prometheus_client import Counter, Histogram, generate_latest

prediction_counter = Counter('predictions_total', 'Total predictions')
prediction_duration = Histogram('prediction_duration_seconds', 'Prediction latency')

@app.get("/metrics")
async def metrics():
    return generate_latest()
```

---

## Troubleshooting

### **Common Issues**

| Issue | Cause | Solution |
|-------|-------|----------|
| **Port 8000 already in use** | Another process using port | `lsof -i :8000` then `kill -9 <PID>` |
| **Database connection refused** | PostgreSQL not running | `docker-compose up postgres` |
| **Model not loading** | Invalid path or format | Verify `MODEL_PATH` in `.env` |
| **High memory usage** | Large batch predictions | Reduce `batch_size` in config |
| **Slow API response** | Missing database indexes | Run `CREATE INDEX` statements |

### **Debug Mode**

```bash
# Enable debug logging
LOG_LEVEL=DEBUG uvicorn backend_app:app --reload

# Verbose database logging
DATABASE_ECHO=True python backend_app.py

# Profiling
pip install py-spy
py-spy record -o profile.svg -- python backend_app.py
```

---

## CI/CD Pipeline

### **GitHub Actions Workflow**

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Backend

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov
    
    - name: Build Docker image
      run: |
        docker build -t spotify-churn-backend:latest .
    
    - name: Push to registry
      if: github.ref == 'refs/heads/main'
      run: |
        docker tag spotify-churn-backend:latest ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
        docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to AWS ECS
      run: |
        aws ecs update-service --cluster spotify-churn --service spotify-churn-api --force-new-deployment
```

---

## Quick Start Checklist

```bash
# ✅ Local Development
□ Python 3.11+ installed
□ Virtual environment created and activated
□ Dependencies installed: pip install -r requirements.txt
□ .env file created with LOCAL settings
□ Database initialized: python -c "from database_layer import db_manager; db_manager.create_tables()"
□ Models loaded in project root
□ Server started and responding to http://localhost:8000/health

# ✅ Docker Development
□ Docker & Docker Compose installed
□ docker-compose.yml reviewed and configured
□ Services started: docker-compose up -d
□ All containers healthy: docker-compose ps
□ API endpoints tested

# ✅ Testing
□ All tests pass: pytest test_integration.py -v
□ Code coverage acceptable: pytest --cov

# ✅ Production
□ Environment variables configured
□ Database backups scheduled
□ SSL/TLS certificates installed
□ Monitoring and logging configured
□ Load balancer/reverse proxy setup
□ CI/CD pipeline configured

# ✅ Security
□ Secrets stored in environment, not in code
□ CORS configured for specific domains
□ Rate limiting enabled
□ Authentication/authorization implemented
□ Input validation on all endpoints
□ SQL injection protection (via ORM)
```

---

## Useful Commands

```bash
# Development
uvicorn backend_app:app --reload
python -m pytest test_integration.py -v

# Docker
docker-compose up -d
docker-compose logs -f backend
docker-compose exec postgres psql -U postgres

# Database
alembic upgrade head
alembic downgrade -1

# Monitoring
curl http://localhost:8000/health
curl http://localhost:8000/metrics

# Testing
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","features":{"subscription_type":"Free"}}'
```

---

## Support & Next Steps

1. **Monitor logs** for production issues
2. **Scale horizontally** by adding more backend instances
3. **Implement caching** for frequently accessed data
4. **Add authentication** for security
5. **Setup alerting** for critical metrics
6. **Document API** with examples and use cases

---

**End of Deployment Guide**

Contact: Role 3 Backend Developer  
Last Updated: 2026-02-26
