# Phase V - Cloud Deployment to DigitalOcean DOKS

## 🎯 Objective
Deploy the Todo application to DigitalOcean Kubernetes (DOKS) with production-ready configuration.

**Points**: 300 base + 600 bonus = **900 points total**

---

## Prerequisites

Before starting, ensure you have:
- ✅ Phase IV completed (local Minikube deployment working)
- ✅ DigitalOcean account created
- ✅ Payment method added to DigitalOcean
- ✅ API token generated (Personal Access Token with read/write scope)

---

## Step 1: Install doctl CLI

### Windows Installation

**Open PowerShell as Administrator** and run:

```powershell
# Download doctl
Invoke-WebRequest https://github.com/digitalocean/doctl/releases/download/v1.146.0/doctl-1.146.0-windows-amd64.zip -OutFile ~\doctl-1.146.0-windows-amd64.zip

# Extract the archive
Expand-Archive -Path ~\doctl-1.146.0-windows-amd64.zip -DestinationPath ~\doctl-1.146.0-windows-amd64

# Create installation directory
New-Item -ItemType Directory $env:ProgramFiles\doctl\ -Force

# Move executable to installation directory
Move-Item -Path ~\doctl-1.146.0-windows-amd64\doctl.exe -Destination $env:ProgramFiles\doctl\ -Force

# Add to system PATH
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::Machine) + ";$env:ProgramFiles\doctl\",
    [EnvironmentVariableTarget]::Machine)

# Refresh current session PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine")
```

### Verify Installation

Close and reopen your terminal, then verify:

```bash
doctl version
```

You should see output like:
```
doctl version 1.146.0-release
Git commit hash: xxxxxxx
Go version: go1.22.x
```

---

## Step 2: Create DigitalOcean API Token

1. Log in to [DigitalOcean Cloud Console](https://cloud.digitalocean.com)
2. Click **API** in the left sidebar
3. Click **Generate New Token**
4. Name: `todo-app-deployment`
5. Scopes: **Read & Write** (both checked)
6. Click **Generate Token**
7. **IMPORTANT**: Copy the token immediately (you won't see it again)

---

## Step 3: Authenticate doctl

```bash
# Initialize doctl with your API token
doctl auth init

# When prompted, paste your API token
# Context name: default (or choose your own)
```

Verify authentication:

```bash
# List your DigitalOcean account info
doctl account get

# List available regions
doctl kubernetes options regions
```

---

## Step 4: Create DOKS Cluster

### Option A: Using doctl CLI (Recommended)

```bash
# Create a Kubernetes cluster
doctl kubernetes cluster create todo-app-cluster \
  --region nyc1 \
  --version 1.31.1-do.5 \
  --node-pool "name=todo-pool;size=s-2vcpu-4gb;count=3;auto-scale=true;min-nodes=2;max-nodes=5" \
  --wait

# This will take 5-10 minutes to provision
```

**Cluster Configuration:**
- **Name**: `todo-app-cluster`
- **Region**: NYC1 (you can choose: `nyc1`, `sfo3`, `sgp1`, `lon1`, `fra1`, `ams3`, etc.)
- **Kubernetes Version**: 1.31.1
- **Node Pool**:
  - Size: `s-2vcpu-4gb` (2 vCPU, 4GB RAM) - $24/month per node
  - Initial nodes: 3
  - Auto-scaling: 2-5 nodes
  - **Estimated cost**: ~$72-120/month depending on scaling

### Option B: Using DigitalOcean Console

1. Go to [DigitalOcean Kubernetes](https://cloud.digitalocean.com/kubernetes/clusters)
2. Click **Create a Kubernetes Cluster**
3. Choose:
   - **Datacenter region**: NYC1 (or nearest to you)
   - **Kubernetes version**: Latest stable (1.31.x)
   - **Node pool**:
     - Name: `todo-pool`
     - Plan: Basic nodes → `s-2vcpu-4gb` ($24/month)
     - Node count: 3
     - Enable autoscaling: 2-5 nodes
4. Click **Create Cluster** (takes 5-10 minutes)

---

## Step 5: Configure kubectl for DOKS

```bash
# Get cluster credentials and configure kubectl
doctl kubernetes cluster kubeconfig save todo-app-cluster

# Verify connection
kubectl cluster-info
kubectl get nodes

# You should see 3 nodes in Ready state
```

**Expected Output:**
```
NAME                        STATUS   ROLES    AGE   VERSION
todo-pool-xxxxx             Ready    <none>   5m    v1.31.1
todo-pool-yyyyy             Ready    <none>   5m    v1.31.1
todo-pool-zzzzz             Ready    <none>   5m    v1.31.1
```

---

## Step 6: Install Nginx Ingress Controller

```bash
# Add ingress-nginx Helm repository
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install Nginx Ingress (creates DigitalOcean Load Balancer)
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/do-loadbalancer-name"=todo-app-lb

# Wait for Load Balancer to be provisioned (2-3 minutes)
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s

# Get the Load Balancer IP
kubectl get svc -n ingress-nginx
```

**Note**: The LoadBalancer costs **$12/month** on DigitalOcean.

---

## Step 7: Update Application Configuration

### Update Backend Configuration

Edit `k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
  namespace: todo-app
data:
  FRONTEND_URL: "https://yourdomain.com"
  CORS_ORIGINS: "https://yourdomain.com,https://www.yourdomain.com"
```

Build the frontend image with `NEXT_PUBLIC_API_URL=/api`; the ingress routes that same-origin prefix to the backend.

### Create Secrets for Production

Generate secure passwords:

```bash
# Generate separate random secrets
python -c "import secrets; print(secrets.token_hex(32))"
```

Create `backend-secrets` and `postgres-secret` in the cluster. Do not store their values in a manifest or ConfigMap.

---

## Step 8: Build and Push Docker Images

### Option A: Use DigitalOcean Container Registry (Recommended)

```bash
# Create a container registry
doctl registry create todo-app-registry

# Login to registry
doctl registry login

# Tag and push backend
cd backend
docker build -t registry.digitalocean.com/todo-app-registry/todo-backend:v1.0.0 .
docker push registry.digitalocean.com/todo-app-registry/todo-backend:v1.0.0

# Tag and push frontend
cd ../frontend
docker build -t registry.digitalocean.com/todo-app-registry/todo-frontend:v1.0.0 .
docker push registry.digitalocean.com/todo-app-registry/todo-frontend:v1.0.0
```

**Registry Cost**: Free for 500MB storage, then $5/month per additional 250GB.

### Option B: Use Docker Hub

```bash
# Login to Docker Hub
docker login

# Tag and push
docker tag todo-backend:local yourusername/todo-backend:v1.0.0
docker tag todo-frontend:local yourusername/todo-frontend:v1.0.0

docker push yourusername/todo-backend:v1.0.0
docker push yourusername/todo-frontend:v1.0.0
```

---

## Step 9: Update Kubernetes Manifests for Cloud

Update image references in deployments:

**`k8s/backend-deployment.yaml`**:
```yaml
spec:
  template:
    spec:
      containers:
      - name: backend
        image: registry.digitalocean.com/todo-app-registry/todo-backend:v1.0.0
        imagePullPolicy: Always  # Changed from Never
```

**`k8s/frontend-deployment.yaml`**:
```yaml
spec:
  template:
    spec:
      containers:
      - name: frontend
        image: registry.digitalocean.com/todo-app-registry/todo-frontend:v1.0.0
        imagePullPolicy: Always  # Changed from Never
```

---

## Step 10: Deploy Application to DOKS

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets from your deployment environment, then apply configmaps
kubectl create secret generic postgres-secret -n todo-app \
  --from-literal=POSTGRES_USER=todo \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  --from-literal=POSTGRES_DB=todo_db
kubectl create secret generic backend-secrets -n todo-app \
  --from-literal=DATABASE_URL="$DATABASE_URL" \
  --from-literal=SECRET_KEY="$SECRET_KEY" \
  --from-literal=SESSION_SECRET="$SESSION_SECRET"
kubectl apply -f k8s/configmap.yaml

# Deploy PostgreSQL
kubectl apply -f k8s/postgres.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=Ready pod -l app=postgres -n todo-app --timeout=120s

# Run database migrations
kubectl apply -f k8s/migration-job.yaml
kubectl wait --for=condition=complete job/db-migration -n todo-app --timeout=300s

# Deploy backend and frontend
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# Deploy ingress
kubectl apply -f k8s/ingress.yaml

# Check deployment status
kubectl get pods -n todo-app
kubectl get svc -n todo-app
kubectl get ingress -n todo-app
```

---

## Step 11: Configure DNS

Get your LoadBalancer IP:

```bash
kubectl get svc -n ingress-nginx
```

Look for the `EXTERNAL-IP` column.

### Configure DNS Records

In your domain registrar (GoDaddy, Namecheap, Cloudflare, etc.):

1. Add **A Record**:
   - Name: `@` (root domain)
   - Value: `<LOAD_BALANCER_IP>`
   - TTL: 300

2. Add **A Record** (API subdomain):
   - Name: `api`
   - Value: `<LOAD_BALANCER_IP>`
   - TTL: 300

3. Add **CNAME Record** (www):
   - Name: `www`
   - Value: `yourdomain.com`
   - TTL: 300

---

## Step 12: Enable HTTPS with cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml

# Wait for cert-manager to be ready
kubectl wait --for=condition=Ready pods --all -n cert-manager --timeout=300s

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com  # Change this
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

Update `k8s/ingress.yaml` with TLS:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: todo-app-ingress
  namespace: todo-app
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - yourdomain.com
    - www.yourdomain.com
    - api.yourdomain.com
    secretName: todo-app-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
```

Apply:
```bash
kubectl apply -f k8s/ingress.yaml
```

Wait 2-5 minutes for certificate to be issued:
```bash
kubectl get certificate -n todo-app
```

---

## Step 13: Enable Monitoring (Optional Bonus)

### Install Prometheus & Grafana

```bash
# Add Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus stack
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin123  # Change this!

# Access Grafana
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80

# Open: http://localhost:3000
# Login: admin / admin123
```

---

## Step 14: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n todo-app

# Check services
kubectl get svc -n todo-app

# Check ingress
kubectl get ingress -n todo-app

# Test backend health
curl https://api.yourdomain.com/health/live

# View logs
kubectl logs -f deployment/backend -n todo-app
kubectl logs -f deployment/frontend -n todo-app
```

---

## Cost Breakdown

| Resource | Specs | Monthly Cost |
|----------|-------|--------------|
| DOKS Nodes (3x) | s-2vcpu-4gb | $72 |
| Load Balancer | 1x | $12 |
| Container Registry | 500MB free | $0 |
| PostgreSQL (managed) | Optional upgrade | $15+ |
| **Total (minimum)** | | **~$84/month** |

**Cost Optimization**:
- Use 2 nodes initially ($48/month)
- Enable autoscaling (2-5 nodes)
- Use DigitalOcean Managed PostgreSQL for production ($15/month)

---

## Troubleshooting

### Pods not starting
```bash
kubectl describe pod <pod-name> -n todo-app
kubectl logs <pod-name> -n todo-app
```

### Cannot pull images
```bash
# Verify registry authentication
doctl registry login

# Check image exists
doctl registry repository list-v2
```

### Ingress not working
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress configuration
kubectl describe ingress todo-app-ingress -n todo-app
```

### Certificate not issued
```bash
# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Check certificate status
kubectl describe certificate todo-app-tls -n todo-app
```

---

## Phase V Checklist

- [ ] doctl installed and authenticated
- [ ] DOKS cluster created (3 nodes)
- [ ] kubectl configured for DOKS
- [ ] Nginx Ingress installed (LoadBalancer created)
- [ ] Docker images pushed to registry
- [ ] Kubernetes manifests updated for cloud
- [ ] Application deployed to DOKS
- [ ] Database migrations applied
- [ ] DNS records configured
- [ ] HTTPS/TLS certificates issued
- [ ] All pods running and healthy
- [ ] Application accessible via domain
- [ ] Monitoring setup (optional)

---

## Phase V Bonus Points

### Available Bonuses (600 points):

1. **kubectl-ai Integration** (200 points)
   - Deploy kubectl-ai for AI-assisted Kubernetes management
   - Configure with OpenAI/Anthropic API

2. **kagent Deployment** (200 points)
   - Deploy Kubernetes agent for automated operations
   - Configure monitoring and alerting

3. **Kafka Event Streaming** (100 points)
   - Deploy Kafka on DOKS
   - Enable Dapr pub/sub
   - Configure event-driven architecture

4. **Dapr Integration** (100 points)
   - Deploy Dapr control plane
   - Enable service mesh
   - Configure state management

---

## Next Steps After Deployment

1. **Test thoroughly**: Create tasks, test all features
2. **Monitor logs**: Watch for errors or performance issues
3. **Set up backups**: Configure PostgreSQL backups
4. **Add monitoring alerts**: Configure Prometheus alerting
5. **Optimize costs**: Review and adjust node counts
6. **Security hardening**: Review RBAC, network policies

---

## Support & Resources

- **DigitalOcean Docs**: https://docs.digitalocean.com/products/kubernetes/
- **kubectl Cheat Sheet**: https://kubernetes.io/docs/reference/kubectl/cheatsheet/
- **Helm Docs**: https://helm.sh/docs/
- **cert-manager Docs**: https://cert-manager.io/docs/

---

**Ready to deploy? Let's start with Step 1!** 🚀
