# Todo Application - Phase IV & V Deployment Guide

## Overview

This guide covers deploying the Todo application to Kubernetes for both local development (Phase IV - Minikube) and cloud production (Phase V - DigitalOcean DOKS).

## Phase IV: Local Kubernetes Deployment (Minikube)

### Prerequisites

- Docker Desktop or Docker Engine installed
- Minikube installed (`minikube version` to verify)
- kubectl installed (`kubectl version --client` to verify)
- Dapr CLI installed (`dapr --version` to verify)
- 4+ CPU cores, 8GB+ RAM available

### Quick Start

```bash
# Make script executable
chmod +x scripts/minikube-setup.sh

# Run setup script
./scripts/minikube-setup.sh
```

This scri  pt will:
1. Start Minikube with 4 CPUs, 8GB memory, docker driver
2. Install Dapr runtime
3. Build backend and frontend Docker images
4. Apply all Kubernetes manifests (namespace, configs, secrets, deployments)
5. Configure local hosts file for `todo.local`

### Verify Deployment

```bash
# Check pod status
kubectl get pods -n todo-app

# Expected output:
# backend-xxxxx         1/1     Running
# frontend-xxxxx        1/1     Running
# postgres-xxxxx        1/1     Running
# kafka-0               1/1     Running

# Check services
kubectl get svc -n todo-app

# Check ingress
kubectl get ingress -n todo-app
```

### Access Application

- **Frontend**: http://todo.local
- **Backend API**: http://todo.local/api
- **Health Check**: http://todo.local/api/health/live

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/backend -n todo-app

# Frontend logs
kubectl logs -f deployment/frontend -n todo-app

# PostgreSQL logs
kubectl logs -f deployment/postgres -n todo-app

# Kafka logs
kubectl logs -f statefulset/kafka -n todo-app
```

### Test Health Endpoints

```bash
# Port forward backend
kubectl port-forward -n todo-app svc/backend 8000:8000

# In another terminal
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

### Test Kafka Events

```bash
# Port forward Kafka
kubectl port-forward -n todo-app svc/kafka 9092:9092

# List topics
kubectl exec -it kafka-0 -n todo-app -- kafka-topics.sh --bootstrap-server localhost:9092 --list

# Consume events
kubectl exec -it kafka-0 -n todo-app -- kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic task-created \
  --from-beginning
```

### Test Dapr

```bash
# Check Dapr sidecar injection
kubectl get pods -n todo-app -o json | jq '.items[].spec.containers[] | select(.name == "daprd")'

# View Dapr logs
dapr logs --kubernetes -n todo-app
```

### Stop Minikube

```bash
minikube stop
```

### Delete Minikube Cluster

```bash
minikube delete
```

---

## Phase V: Cloud Deployment (DigitalOcean DOKS)

### Prerequisites

- DigitalOcean account with API token
- doctl CLI installed (installed by setup script)
- Docker Hub account or private registry
- Domain name (for ingress)

### Quick Start

```bash
# Make script executable
chmod +x scripts/do-setup.sh

# Run setup script
./scripts/do-setup.sh
```

When prompted:
1. Enter your DigitalOcean API token
2. Wait for cluster creation (5-10 minutes)
3. Script will handle the rest (ingress, cert-manager, Dapr, Helm deployment)

### Manual Deployment Steps (if needed)

```bash
# Authenticate with DigitalOcean
doctl auth init

# Create DOKS cluster
doctl kubernetes cluster create \
  todo-cluster \
  --region nyc3 \
  --version latest \
  --node-pool "name=worker-pool;size=s-2vcpu-4gb;count=3"

# Get kubeconfig
doctl kubernetes cluster kubeconfig save todo-cluster

# Install NGINX Ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/do/deploy.yaml

# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Install Dapr
dapr init --runtime-version=1.13.0 --kubernetes --helm-chart-version=1.13.0

# Push images to registry
docker push your-registry/todo-backend:latest
docker push your-registry/todo-frontend:latest

# Deploy with Helm
helm install todo-app helm/todo-app \
  --namespace todo-app \
  --create-namespace \
  --values helm/todo-app/values.yaml \
  --set ingress.host=your-domain.com \
  --set image.backend.repository=your-registry/todo-backend \
  --set image.frontend.repository=your-registry/todo-frontend
```

### Verify Cloud Deployment

```bash
# Check cluster status
doctl kubernetes cluster get todo-cluster

# Get ingress IP
kubectl get ingress -n todo-app
# Note: IP will be LoadBalancer IP from DigitalOcean

# Check pod status
kubectl get pods -n todo-app

# Check services
kubectl get svc -n todo-app

# Check HPA status
kubectl get hpa -n todo-app
```

### Configure DNS

After getting the LoadBalancer IP from the ingress, update your DNS provider:
```
A record: your-domain.com → <LoadBalancer IP>
```

### Access Application

- **Frontend**: https://your-domain.com
- **Backend API**: https://your-domain.com/api
- **Health Check**: https://your-domain.com/api/health/live

### Monitoring

Access Grafana for monitoring:
```bash
# Get Grafana LoadBalancer IP
kubectl get svc -n monitoring

# Login with admin / admin (default credentials)
```

### Upgrade Deployment

```bash
helm upgrade todo-app helm/todo-app \
  --namespace todo-app \
  --values helm/todo-app/values.yaml
```

### Rollback Deployment

```bash
helm rollback todo-app
```

### Delete Cloud Deployment

```bash
# Delete Helm release
helm uninstall todo-app -n todo-app

# Delete cluster
doctl kubernetes cluster delete todo-cluster
```

---

## Environment Variables

### Backend (.env)

```env
DATABASE_URL=postgresql://todo:todo@postgres:5432/todo_db
SECRET_KEY=your-secret-key
SESSION_SECRET=your-session-secret
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Troubleshooting

### Pods not starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n todo-app

# Check pod logs
kubectl logs <pod-name> -n todo-app

# Check resource usage
kubectl top nodes
kubectl top pods -n todo-app
```

### Database connection issues

```bash
# Port forward PostgreSQL
kubectl port-forward -n todo-app svc/postgres 5432:5432

# Test connection
psql -h localhost -U todo -d todo_db
```

### Ingress not working

```bash
# Check ingress status
kubectl get ingress -n todo-app
kubectl describe ingress todo-app-ingress -n todo-app

# Check ingress controller
kubectl get pods -n ingress-nginx

# For Minikube, ensure hosts file updated
cat /etc/hosts | grep todo.local
```

### Dapr not working

```bash
# Check Dapr installation
dapr status --kubernetes

# Check Dapr sidecar logs
kubectl logs <pod-name> -c daprd -n todo-app

# Restart Dapr
dapr uninstall --all
dapr init --runtime-version=1.13.0 --kubernetes
```

### HPA not scaling

```bash
# Check HPA status
kubectl get hpa -n todo-app
kubectl describe hpa backend-hpa -n todo-app

# Check metrics-server
kubectl get deployment metrics-server -n kube-system

# For Minikube, ensure metrics addon enabled
minikube addons list | grep metrics
```

---

## Performance Tuning

### Resource Limits

Adjust resource requests/limits in `helm/todo-app/values.yaml`:

```yaml
resources:
  backend:
    requests:
      memory: 256Mi
      cpu: 250m
    limits:
      memory: 512Mi
      cpu: 500m
```

### Database Connection Pool

Modify in backend deployment to increase connections:

```yaml
DATABASE_POOL_SIZE: "20"
DATABASE_ECHO: "false"
```

### Kafka Partitions

For better throughput, increase Kafka partitions:

```bash
kubectl exec -it kafka-0 -n todo-app -- kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --alter \
  --topic task-created \
  --partitions 3
```

---

## Security Best Practices

### Secrets Management

- Use Kubernetes Secrets for development
- Use HashiCorp Vault for production
- Never commit secrets to git
- Rotate secrets regularly

### RBAC

Apply least-privilege RBAC:

```bash
kubectl apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: todo-app-reader
  namespace: todo-app
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: pod-reader
subjects:
- kind: ServiceAccount
  name: default
  namespace: todo-app
EOF
```

### Network Policies

Restrict inter-pod communication:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: todo-app-network-policy
  namespace: todo-app
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
```

### TLS/SSL

- Enable TLS for all services (automatically via cert-manager in cloud)
- Use strong ciphers
- Keep certificates updated

---

## Bonus Features

### kubectl-ai

AI-powered Kubernetes commands:

```bash
# Install
curl -sSL https://raw.githubusercontent.com/kubernetes/kubectl-ai/main/install.sh | bash

# Usage
kubectl-ai "Why is the backend pod failing?"
kubectl-ai "Scale up frontend to 5 replicas"
kubectl-ai "Show me the resource usage of all pods"
```

### kagent

Autonomous Kubernetes operations:

```bash
# Check kagent status
kubectl logs -f deployment/kagent -n todo-app

# View decisions
kubectl describe pod <kagent-pod> -n todo-app
```

### Voice Commands

Use the Voice Command button in the dashboard to create tasks via voice:

1. Click the microphone icon
2. Speak your task (e.g., "Create a task to review pull requests with high priority")
3. The backend parses the voice input using LLM
4. Task is created automatically

---

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Dapr Documentation](https://docs.dapr.io/)
- [DigitalOcean DOKS Documentation](https://docs.digitalocean.com/products/kubernetes/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
