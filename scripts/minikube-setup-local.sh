#!/bin/bash

set -e

echo "Starting Minikube setup (Solution 2: Local Build)..."

# Start Minikube with required resources
echo "Starting Minikube cluster..."
minikube start \
  --cpus=4 \
  --memory=6144 \
  --disk-size=40GB \
  --driver=docker \
  --addons=ingress \
  --addons=metrics-server

# Enable Dapr
echo "Installing Dapr..."
dapr uninstall --all --kubernetes || true
dapr init --kubernetes --runtime-version 1.13.0 --wait

echo ""
echo "Building Docker images LOCALLY first..."
echo "=========================================="

# Build backend image locally
echo "Building backend image locally..."
cd backend
docker build -t todo-backend:local .

# Build frontend image locally (uses host docker)
echo "Building frontend image locally..."
cd ../frontend
docker build -t todo-frontend:local .
cd ..

echo ""
echo "Loading images into Minikube..."
echo "=========================================="

# Load images into Minikube
echo "Loading backend image to Minikube..."
minikube image load todo-backend:local

echo "Loading frontend image to Minikube..."
minikube image load todo-frontend:local

# Tag images for k8s to use
echo "Retagging images for Kubernetes..."
kubectl delete image todo-backend:local -n todo-app 2>/dev/null || true
kubectl delete image todo-frontend:local -n todo-app 2>/dev/null || true

echo ""
echo "Applying Kubernetes manifests..."
echo "=========================================="

kubectl apply -f k8s/namespace.yaml
sleep 2

kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

echo "Deploying PostgreSQL..."
kubectl apply -f k8s/postgres.yaml
sleep 5

echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n todo-app --timeout=300s

echo "Deploying services..."
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

echo "Deploying Kafka..."
kubectl apply -f k8s/kafka.yaml
sleep 5

# Apply Dapr components
echo "Applying Dapr components..."
kubectl apply -f k8s/dapr-components/

# Configure todo.local in hosts (platform-specific)
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Linux detected - adding to /etc/hosts"
    echo "$MINIKUBE_IP todo.local" | sudo tee -a /etc/hosts
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS detected - adding to /etc/hosts"
    echo "$MINIKUBE_IP todo.local" | sudo tee -a /etc/hosts
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    echo "Windows detected - manual step required"
    echo "Please add the following to C:\\Windows\\System32\\drivers\\etc\\hosts:"
    echo "$MINIKUBE_IP todo.local"
fi

echo ""
echo "✅ Minikube setup complete!"
echo "Minikube IP: $MINIKUBE_IP"
echo "Access app at: http://todo.local"
echo ""
echo "Check pod status:"
echo "kubectl get pods -n todo-app"
echo ""
echo "Check service status:"
echo "kubectl get svc -n todo-app"
echo ""
echo "Check ingress status:"
echo "kubectl get ingress -n todo-app"
echo ""
echo "View backend logs:"
echo "kubectl logs -f deployment/backend -n todo-app"
echo ""
echo "View frontend logs:"
echo "kubectl logs -f deployment/frontend -n todo-app"
