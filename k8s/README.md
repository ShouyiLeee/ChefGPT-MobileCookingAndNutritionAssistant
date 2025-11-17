# Kubernetes Deployment for ChefGPT

This directory contains Kubernetes manifests for deploying the ChefGPT backend to a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (v1.24+)
- `kubectl` configured to access your cluster
- Nginx Ingress Controller installed
- cert-manager (optional, for automatic SSL certificates)
- Sufficient cluster resources

## Quick Start

### 1. Update Configuration

Before deploying, update the following files with your actual values:

**`secret.yaml`:**
- Database passwords
- API keys (OpenAI, Anthropic)
- JWT secrets
- Redis password

**`backend-deployment.yaml` and `celery-worker-deployment.yaml`:**
- Replace `your-docker-registry/chefgpt-backend:latest` with your actual Docker image

**`ingress.yaml`:**
- Replace `api.chefgpt.com` with your actual domain

### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Deploy configuration and secrets
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml

# Deploy database and Redis
kubectl apply -f postgres-pvc.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f redis-deployment.yaml

# Wait for database to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n chefgpt --timeout=300s

# Deploy backend
kubectl apply -f backend-deployment.yaml

# Deploy Celery workers
kubectl apply -f celery-worker-deployment.yaml

# Deploy ingress
kubectl apply -f ingress.yaml

# Deploy autoscaling
kubectl apply -f hpa.yaml
```

### 3. Using Kustomize (Alternative)

```bash
# Deploy everything at once
kubectl apply -k .

# Or build and preview
kubectl kustomize . | kubectl apply -f -
```

## Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n chefgpt

# Check services
kubectl get svc -n chefgpt

# Check ingress
kubectl get ingress -n chefgpt

# View logs
kubectl logs -f deployment/chefgpt-backend -n chefgpt
```

## Database Migrations

Run database migrations after first deployment:

```bash
kubectl exec -it deployment/chefgpt-backend -n chefgpt -- alembic upgrade head
```

## Seed Database

```bash
kubectl exec -it deployment/chefgpt-backend -n chefgpt -- python scripts/seed_recipes.py
kubectl exec -it deployment/chefgpt-backend -n chefgpt -- python scripts/reindex_recipes.py
```

## Scaling

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment chefgpt-backend --replicas=5 -n chefgpt

# Scale Celery workers
kubectl scale deployment celery-worker --replicas=4 -n chefgpt
```

### Auto Scaling

HPA (Horizontal Pod Autoscaler) is configured to automatically scale based on CPU and memory usage:

- Backend: 3-10 replicas
- Celery Workers: 2-8 replicas

View HPA status:

```bash
kubectl get hpa -n chefgpt
```

## Updating the Application

### Rolling Update

```bash
# Update backend image
kubectl set image deployment/chefgpt-backend backend=your-registry/chefgpt-backend:v1.1.0 -n chefgpt

# Check rollout status
kubectl rollout status deployment/chefgpt-backend -n chefgpt

# Rollback if needed
kubectl rollout undo deployment/chefgpt-backend -n chefgpt
```

## Monitoring

### Check Resource Usage

```bash
# Pod resource usage
kubectl top pods -n chefgpt

# Node resource usage
kubectl top nodes
```

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/chefgpt-backend -n chefgpt

# Celery worker logs
kubectl logs -f deployment/celery-worker -n chefgpt

# Database logs
kubectl logs -f deployment/postgres -n chefgpt
```

## Troubleshooting

### Pod Not Starting

```bash
# Describe pod
kubectl describe pod <pod-name> -n chefgpt

# Check events
kubectl get events -n chefgpt --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Test database connection
kubectl exec -it deployment/postgres -n chefgpt -- psql -U postgres -d chefgpt

# Check database service
kubectl get svc postgres-service -n chefgpt
```

### Ingress Not Working

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Describe ingress
kubectl describe ingress chefgpt-ingress -n chefgpt

# Check ingress logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

## Backup and Restore

### Backup Database

```bash
# Create backup
kubectl exec deployment/postgres -n chefgpt -- pg_dump -U postgres chefgpt > backup.sql
```

### Restore Database

```bash
# Restore from backup
kubectl exec -i deployment/postgres -n chefgpt -- psql -U postgres chefgpt < backup.sql
```

## SSL/TLS Configuration

If using cert-manager for automatic SSL:

1. Install cert-manager:
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

2. Create ClusterIssuer:
```bash
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Cleanup

```bash
# Delete all resources
kubectl delete -k .

# Or delete individually
kubectl delete namespace chefgpt
```

## Production Best Practices

1. **Secrets Management**: Use external secret management (e.g., Sealed Secrets, External Secrets Operator, or HashiCorp Vault)

2. **Monitoring**: Install Prometheus and Grafana for comprehensive monitoring

3. **Logging**: Use EFK/ELK stack or Loki for centralized logging

4. **Backups**: Set up automated database backups with CronJobs

5. **Resource Limits**: Always set resource requests and limits

6. **Network Policies**: Implement network policies for pod-to-pod communication

7. **Pod Disruption Budgets**: Configure PDBs to prevent too many pods from going down during updates

8. **Security**: Use Pod Security Standards/Policies

## Cloud-Specific Notes

### AWS EKS

- Use `gp3` storage class for better performance
- Use AWS Load Balancer Controller for ingress
- Consider using RDS for PostgreSQL instead of in-cluster

### GCP GKE

- Use `pd-ssd` for better disk performance
- Enable Workload Identity for secure API access
- Consider using Cloud SQL for PostgreSQL

### Azure AKS

- Use `managed-premium` storage class
- Use Azure Application Gateway for ingress
- Consider using Azure Database for PostgreSQL

## Support

For issues or questions, refer to:
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Nginx Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
