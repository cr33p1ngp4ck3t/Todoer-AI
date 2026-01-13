#!/bin/bash

set -e

echo "Starting DigitalOcean DOKS setup..."

# Install doctl
echo "Installing doctl CLI..."
if ! command -v doctl &> /dev/null; then
    curl -sSL https://digitalocean.com/doctl/install.sh | sh
    export PATH=$PATH:/root/.doctl/bin
fi

# Authenticate
echo "Authenticating with DigitalOcean..."
echo "Please provide your DigitalOcean API token:"
read DO_TOKEN
doctl auth init --access-token "$DO_TOKEN"

# Create DOKS cluster
echo "Creating DOKS cluster (todo-cluster)..."
doctl kubernetes cluster create \
  todo-cluster \
  --region nyc3 \
  --version latest \
  --node-pool "name=worker-pool;size=s-2vcpu-4gb;count=3;auto-scale=true;min-nodes=2;max-nodes=5"

# Wait for cluster to be ready
echo "Waiting for cluster to be ready..."
sleep 60

# Get cluster credentials
echo "Configuring kubectl..."
doctl kubernetes cluster kubeconfig save todo-cluster

# Install NGINX Ingress Controller
echo "Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/do/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=120s

# Install cert-manager for TLS
echo "Installing cert-manager..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
kubectl wait --namespace cert-manager --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager --timeout=120s

# Create ClusterIssuer for Let's Encrypt
echo "Creating Let's Encrypt ClusterIssuer..."
kubectl apply -f - <<EOF
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

# Install Dapr
echo "Installing Dapr..."
if ! command -v dapr &> /dev/null; then
    wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash
    export PATH=$PATH:$HOME/.dapr/bin
fi

dapr uninstall --all || true
dapr init --runtime-version=1.13.0 --kubernetes --helm-chart-version=1.13.0

# Create namespace
echo "Creating todo-app namespace..."
kubectl create namespace todo-app || true

# Build and push images to Docker Hub (or your registry)
echo "Building Docker images..."

cd backend
echo "Building backend image..."
docker build -t your-registry/todo-backend:latest .
docker push your-registry/todo-backend:latest
cd ..

cd frontend
echo "Building frontend image..."
docker build -t your-registry/todo-frontend:latest .
docker push your-registry/todo-frontend:latest
cd ..

# Deploy with Helm
echo "Deploying application with Helm..."
helm install todo-app helm/todo-app \
  --namespace todo-app \
  --values helm/todo-app/values.yaml \
  --set cloud.provider=digitalocean \
  --set cloud.region=nyc3 \
  --set ingress.host=your-domain.com \
  --set image.backend.repository=your-registry/todo-backend \
  --set image.frontend.repository=your-registry/todo-frontend \
  --set monitoring.enabled=true

echo ""
echo "✅ DigitalOcean DOKS setup complete!"
echo ""
echo "Cluster info:"
doctl kubernetes cluster get todo-cluster
echo ""
echo "Get cluster IP:"
kubectl get ingress -n todo-app
echo ""
echo "Check pod status:"
echo "kubectl get pods -n todo-app"
echo ""
echo "Check service status:"
echo "kubectl get svc -n todo-app"
echo ""
echo "View backend logs:"
echo "kubectl logs -f deployment/todo-app-backend -n todo-app"
echo ""
echo "View frontend logs:"
echo "kubectl logs -f deployment/todo-app-frontend -n todo-app"
