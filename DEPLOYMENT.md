# ChefGPT Deployment Guide

Complete deployment guide for the ChefGPT mobile cooking and nutrition assistant application.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Development Deployment](#development-deployment)
- [Staging Deployment](#staging-deployment)
- [Production Deployment](#production-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring and Maintenance](#monitoring-and-maintenance)

## Overview

ChefGPT consists of:
- **Backend**: FastAPI application with RAG-powered recipe search
- **Mobile**: Flutter cross-platform mobile application
- **Database**: PostgreSQL with pgvector extension
- **Cache**: Redis for caching and task queue
- **Workers**: Celery workers for background tasks

## Prerequisites

### Required Software

- Docker 20.10+
- Docker Compose 2.0+
- Git
- Make (optional, for convenience commands)

### For Kubernetes Deployment

- Kubernetes cluster (1.24+)
- kubectl configured
- Nginx Ingress Controller
- cert-manager (for SSL)

### Required Credentials

- OpenAI API key
- Anthropic API key (optional)
- Supabase account (optional)
- Docker Hub account (for production images)

## Development Deployment

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/your-org/chefgpt.git
cd chefgpt
```

2. **Set up environment variables**
```bash
cd backend
cp .env.example .env
# Edit .env with your API keys
```

3. **Start development environment**
```bash
# Using Make
make dev

# Or using Docker Compose directly
docker-compose -f docker-compose.dev.yml up -d
```

4. **Run database migrations**
```bash
make migrate
# Or: docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

5. **Seed sample data**
```bash
make seed
```

6. **Access the application**
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Database UI (Adminer): http://localhost:8080
- Redis UI: http://localhost:8081

### Development Commands

```bash
# View logs
make logs

# Open backend shell
make shell

# Run tests
make test

# Run linters
make lint

# Stop all services
make down

# Clean everything (including volumes)
make clean
```

## Staging Deployment

### Using Docker Compose

1. **Prepare staging environment file**
```bash
cd backend
cp .env.staging .env.staging
# Update with staging credentials
```

2. **Deploy to staging**
```bash
./backend/scripts/deploy.sh staging
```

### Manual Deployment on Staging Server

1. **SSH to staging server**
```bash
ssh user@staging.chefgpt.com
```

2. **Pull latest code**
```bash
cd /opt/chefgpt
git pull origin develop
```

3. **Deploy**
```bash
./backend/scripts/deploy.sh staging
```

4. **Check health**
```bash
./backend/scripts/health-check.sh staging
```

## Production Deployment

### Option 1: Docker Compose Deployment

#### Initial Setup

1. **Prepare production server**
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Clone repository on production server**
```bash
cd /opt
sudo git clone https://github.com/your-org/chefgpt.git
cd chefgpt
```

3. **Configure environment**
```bash
cd backend
sudo cp .env.production .env.production
sudo nano .env.production
# Update all placeholder values with production credentials
```

4. **Configure SSL certificates** (if using Nginx)
```bash
# Place SSL certificates
sudo mkdir -p backend/nginx/ssl
sudo cp /path/to/fullchain.pem backend/nginx/ssl/
sudo cp /path/to/privkey.pem backend/nginx/ssl/
```

5. **Deploy**
```bash
sudo ./backend/scripts/deploy.sh production
```

#### Automated Deployment

Use the deployment script for automated deployments:

```bash
# Deploy to production
sudo ./backend/scripts/deploy.sh production

# The script will:
# - Create database backup
# - Pull latest changes
# - Build Docker images
# - Run database migrations
# - Start services
# - Check health
```

#### Rollback

If something goes wrong:

```bash
# List available backups
ls -lh backend/backups/

# Rollback to previous version
sudo ./backend/scripts/rollback.sh production backend/backups/backup_20240115_120000.sql
```

### Option 2: Kubernetes Deployment

See [Kubernetes Deployment](#kubernetes-deployment) section below.

### Production Checklist

Before deploying to production:

- [ ] Update all secrets in `.env.production`
- [ ] Configure SSL certificates
- [ ] Set up DNS records pointing to your server
- [ ] Configure firewall (allow ports 80, 443)
- [ ] Set up automated backups
- [ ] Configure monitoring and alerting
- [ ] Test on staging environment first
- [ ] Create database backup
- [ ] Notify team about deployment

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (AWS EKS, GCP GKE, Azure AKS, or self-hosted)
- kubectl configured to access the cluster
- Nginx Ingress Controller installed
- cert-manager installed (for automatic SSL)

### Quick Deploy

1. **Update configurations**
```bash
cd k8s
```

Edit the following files:
- `secret.yaml` - Add all secrets and API keys
- `backend-deployment.yaml` - Update Docker image registry
- `celery-worker-deployment.yaml` - Update Docker image registry
- `ingress.yaml` - Update domain name

2. **Deploy using kubectl**
```bash
# Deploy all resources
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f postgres-pvc.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f redis-deployment.yaml

# Wait for database
kubectl wait --for=condition=ready pod -l app=postgres -n chefgpt --timeout=300s

# Deploy backend
kubectl apply -f backend-deployment.yaml
kubectl apply -f celery-worker-deployment.yaml
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml
```

3. **Or deploy using Kustomize**
```bash
kubectl apply -k k8s/
```

4. **Run migrations**
```bash
kubectl exec -it deployment/chefgpt-backend -n chefgpt -- alembic upgrade head
```

5. **Seed database**
```bash
kubectl exec -it deployment/chefgpt-backend -n chefgpt -- python scripts/seed_recipes.py
```

### Verify Deployment

```bash
# Check pods
kubectl get pods -n chefgpt

# Check services
kubectl get svc -n chefgpt

# Check ingress
kubectl get ingress -n chefgpt

# View logs
kubectl logs -f deployment/chefgpt-backend -n chefgpt
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment chefgpt-backend --replicas=5 -n chefgpt

# Auto-scaling is configured via HPA (3-10 replicas)
kubectl get hpa -n chefgpt
```

### Updates

```bash
# Rolling update
kubectl set image deployment/chefgpt-backend backend=your-registry/chefgpt-backend:v1.1.0 -n chefgpt

# Check rollout status
kubectl rollout status deployment/chefgpt-backend -n chefgpt

# Rollback if needed
kubectl rollout undo deployment/chefgpt-backend -n chefgpt
```

See [k8s/README.md](k8s/README.md) for detailed Kubernetes documentation.

## CI/CD Pipeline

### GitHub Actions

The project includes automated CI/CD pipelines:

#### On Pull Request / Push to develop
- Backend tests and linting
- Security scanning
- Docker image building
- Mobile app build and test

#### On Push to develop
- Auto-deploy to staging environment

#### On Push to main
- Auto-deploy to production environment

### Setup GitHub Secrets

Configure the following secrets in your GitHub repository:

```
# Docker Hub
DOCKER_USERNAME
DOCKER_PASSWORD

# OpenAI & Anthropic
OPENAI_API_KEY
ANTHROPIC_API_KEY

# Staging Server
STAGING_HOST
STAGING_USER
STAGING_SSH_KEY

# Production Server
PRODUCTION_HOST
PRODUCTION_USER
PRODUCTION_SSH_KEY

# Mobile Signing (for releases)
ANDROID_SIGNING_KEY
ANDROID_KEY_ALIAS
ANDROID_KEYSTORE_PASSWORD
ANDROID_KEY_PASSWORD
```

### Manual Workflow Trigger

Workflows can also be triggered manually from the GitHub Actions tab.

## Monitoring and Maintenance

### Health Checks

```bash
# Check all services
./backend/scripts/health-check.sh production

# Check specific service
curl https://api.chefgpt.com/health
```

### Viewing Logs

**Docker Compose:**
```bash
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f celery-worker
```

**Kubernetes:**
```bash
kubectl logs -f deployment/chefgpt-backend -n chefgpt
kubectl logs -f deployment/celery-worker -n chefgpt
```

### Database Backup

**Docker Compose:**
```bash
# Manual backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres chefgpt > backup_$(date +%Y%m%d).sql
```

**Kubernetes:**
```bash
kubectl exec deployment/postgres -n chefgpt -- pg_dump -U postgres chefgpt > backup_$(date +%Y%m%d).sql
```

### Common Issues

#### Database Connection Errors
```bash
# Check database status
docker-compose ps db
# Or: kubectl get pods -l app=postgres -n chefgpt

# Check database logs
docker-compose logs db
# Or: kubectl logs -l app=postgres -n chefgpt
```

#### High Memory Usage
```bash
# Check container stats
docker stats

# Or Kubernetes
kubectl top pods -n chefgpt
```

#### SSL Certificate Issues
```bash
# Check certificate expiry
openssl s_client -connect api.chefgpt.com:443 -servername api.chefgpt.com | openssl x509 -noout -dates
```

## Performance Tuning

### Backend Scaling

**Docker Compose:**
Update `docker-compose.prod.yml`:
```yaml
backend:
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 8
```

**Kubernetes:**
Adjust HPA settings in `k8s/hpa.yaml`

### Database Optimization

```sql
-- Create indexes for frequently queried fields
CREATE INDEX idx_recipes_cuisine ON recipes(cuisine);
CREATE INDEX idx_recipes_difficulty ON recipes(difficulty);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM recipes WHERE cuisine = 'vietnamese';
```

### Redis Configuration

Adjust Redis memory limits:
```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

## Security Best Practices

1. **Secrets Management**
   - Never commit secrets to git
   - Use environment variables
   - Consider using secrets management tools (Vault, AWS Secrets Manager, etc.)

2. **SSL/TLS**
   - Always use HTTPS in production
   - Use cert-manager for automatic certificate renewal
   - Set up HSTS headers

3. **Firewall**
   - Only expose ports 80 and 443
   - Use VPN for database access
   - Implement rate limiting

4. **Updates**
   - Keep Docker images updated
   - Regularly update dependencies
   - Monitor security advisories

5. **Backups**
   - Automate daily backups
   - Test restore procedures
   - Store backups off-site

## Support and Documentation

- **Backend API Documentation**: https://api.chefgpt.com/docs
- **Project Repository**: https://github.com/your-org/chefgpt
- **Kubernetes Guide**: [k8s/README.md](k8s/README.md)
- **RAG Pipeline**: [backend/RAG_README.md](backend/RAG_README.md)

## License

[Your License]

## Contact

For issues or questions:
- Open an issue on GitHub
- Email: support@chefgpt.com
