#!/bin/bash

set -e

echo "Starting Minikube setup..."

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

# Build and push images to Minikube registry
echo "Building Docker images..."
eval $(minikube docker-env)

cd backend
echo "Building backend image..."
docker build -t todo-backend:latest .
cd ..

cd frontend
echo "Building frontend image..."
docker build -t todo-frontend:latest .
cd ..

# Apply Kubernetes manifests
echo "Applying Kubernetes manifests..."
kubectl apply -f k8s/namespace.yaml
sleep 2

kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

echo "Deploying PostgreSQL..."
kubectl apply -f k8s/postgres.yaml
sleep 5

echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n todo-app --timeout=300s

echo "Deploying backend..."
kubectl apply -f k8s/backend-deployment.yaml
sleep 3

echo "Deploying frontend..."
kubectl apply -f k8s/frontend-deployment.yaml
sleep 3

echo "Deploying Kafka..."
kubectl apply -f k8s/kafka.yaml
sleep 5

echo "Setting up Ingress..."
kubectl apply -f k8s/ingress.yaml

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
