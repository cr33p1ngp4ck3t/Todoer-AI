# Phase V - Hybrid Cloud Deployment (100% FREE)

## 🎯 Architecture Overview

**Frontend**: Render.com (Static Site - Free, Unlimited, Fast CDN)
**Backend**: Oracle Cloud + K3s (Free Forever, 24GB RAM)
**Database**: Oracle Cloud PostgreSQL (Free Forever, Persistent)

**Total Cost**: **$0/month FOREVER** ✅

---

## 📊 Why Hybrid Approach?

| Component | Platform | Why? | Resources |
|-----------|----------|------|-----------|
| **Frontend** | Render | Fast CDN, no cold starts, free static sites | Unlimited |
| **Backend** | Oracle Cloud | 24GB RAM, always on, full K3s | 4 cores, 24GB |
| **Database** | Oracle Cloud | Persistent, always on, production-ready | Included |

**Benefits:**
- ✅ Best performance (frontend on CDN, backend on powerful VM)
- ✅ No cold starts (both always running)
- ✅ No resource limits (24GB RAM for backend!)
- ✅ Free forever (no expiry)
- ✅ Production ready

---

## Part 1: Oracle Cloud Setup (Backend + Database)

### Step 1: Create Oracle Cloud Account

1. Go to: https://signup.cloud.oracle.com/
2. Fill in details:
   - Email address
   - Country/Territory
   - First and Last Name
3. **Verify your email**
4. **Complete account setup**:
   - Home region (choose closest: US East, US West, UK, Germany, etc.)
   - ⚠️ **Cannot change home region later!**
   - Add credit card (for verification only - won't be charged)
5. Wait for account activation (usually instant, sometimes 30min)

### Step 2: Create Ampere A1 VM Instance

1. **Log in to Oracle Cloud Console**: https://cloud.oracle.com/
2. Click **"Create a VM instance"** or go to Compute > Instances
3. **Configure instance**:

```yaml
Name: todo-app-backend
Placement:
  - Availability domain: AD-1 (or any available)
  - Fault domain: (leave default)

Image and shape:
  - Image: Ubuntu 22.04 (or latest Ubuntu)
  - Click "Change shape"
  - Select: "Ampere" (ARM-based)
  - Shape: VM.Standard.A1.Flex
  - OCPUs: 4
  - Memory: 24 GB
  ✅ This is 100% free (Always Free tier)

Networking:
  - VCN: Create new VCN (or use default)
  - Subnet: Create public subnet
  - Public IP: Assign a public IPv4 address ✅

Add SSH keys:
  - Generate a key pair OR
  - Upload your existing SSH public key
  ⚠️ SAVE THE PRIVATE KEY! You'll need it to connect
```

4. **Open required ports**:
   - After instance creation, go to VCN > Security Lists
   - Click default security list
   - Add Ingress Rules:

```yaml
Rule 1 (SSH):
  - Source CIDR: 0.0.0.0/0
  - Destination Port: 22
  - Protocol: TCP

Rule 2 (HTTP):
  - Source CIDR: 0.0.0.0/0
  - Destination Port: 80
  - Protocol: TCP

Rule 3 (HTTPS):
  - Source CIDR: 0.0.0.0/0
  - Destination Port: 443
  - Protocol: TCP

Rule 4 (Backend API):
  - Source CIDR: 0.0.0.0/0
  - Destination Port: 8000
  - Protocol: TCP

Rule 5 (Kubernetes API):
  - Source CIDR: 0.0.0.0/0
  - Destination Port: 6443
  - Protocol: TCP
```

5. Click **"Create"**
6. Wait 2-3 minutes for instance to provision
7. **Note down the Public IP address**

### Step 3: Connect to Your VM

**On Windows (using PowerShell):**
```powershell
# If using generated key pair, first set permissions
icacls "C:\path\to\ssh-key-private.key" /inheritance:r
icacls "C:\path\to\ssh-key-private.key" /grant:r "%username%:R"

# Connect to VM
ssh -i "C:\path\to\ssh-key-private.key" ubuntu@<PUBLIC_IP>
```

**First time connection:**
```bash
# You'll see: "Are you sure you want to continue connecting (yes/no)?"
# Type: yes
```

### Step 4: Install K3s on Oracle Cloud VM

Once connected to your VM:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl wget git

# Install K3s (lightweight Kubernetes)
curl -sfL https://get.k3s.io | sh -

# Wait for K3s to be ready (30 seconds)
sudo k3s kubectl get nodes

# You should see your node in "Ready" state
```

**Set up kubectl access:**
```bash
# Create .kube directory
mkdir -p ~/.kube

# Copy K3s config to kubectl config
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config

# Update server IP in config
sed -i "s/127.0.0.1/<YOUR_PUBLIC_IP>/g" ~/.kube/config

# Test kubectl
kubectl get nodes
```

### Step 5: Deploy Backend and Database to K3s

**Create namespace:**
```bash
kubectl create namespace todo-app
```

**Deploy PostgreSQL:**
```bash
# Create postgres.yaml on VM
cat > postgres.yaml << 'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: todo-app
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: todo-app
type: Opaque
stringData:
  POSTGRES_USER: todo
  POSTGRES_PASSWORD: your-secure-password-here  # Change this!
  POSTGRES_DB: todo_db
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: todo-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: POSTGRES_PASSWORD
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: POSTGRES_DB
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: todo-app
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
EOF

# Apply PostgreSQL
kubectl apply -f postgres.yaml

# Wait for postgres to be ready
kubectl wait --for=condition=Ready pod -l app=postgres -n todo-app --timeout=120s
```

**Push Backend Docker Image to Docker Hub:**

On your **local machine** (not the VM):

```bash
# Login to Docker Hub
docker login

# Tag your backend image
docker tag todo-backend:local yourusername/todo-backend:v1.0.0

# Push to Docker Hub
docker push yourusername/todo-backend:v1.0.0
```

**Deploy Backend to K3s:**

Back on the **Oracle Cloud VM**:

```bash
# Create backend deployment
cat > backend.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
  namespace: todo-app
data:
  DATABASE_URL: "postgresql://todo:your-secure-password-here@postgres:5432/todo_db"
  ENVIRONMENT: "production"
  LOG_LEVEL: "info"
  CORS_ORIGINS: "*"  # Will update this after getting Render URL
---
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
  namespace: todo-app
type: Opaque
stringData:
  SECRET_KEY: "your-super-secret-key-here"  # Generate with: openssl rand -hex 32
  OPENAI_API_KEY: "your-openai-key"  # Optional
  GEMINI_API_KEY: "your-gemini-key"  # Optional
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: todo-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      initContainers:
      - name: run-migrations
        image: yourusername/todo-backend:v1.0.0  # Update with your image
        command: ["alembic", "upgrade", "head"]
        envFrom:
        - configMapRef:
            name: backend-config
        - secretRef:
            name: backend-secrets
      containers:
      - name: backend
        image: yourusername/todo-backend:v1.0.0  # Update with your image
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: backend-config
        - secretRef:
            name: backend-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: todo-app
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer  # K3s will expose on node port
EOF

# Apply backend
kubectl apply -f backend.yaml

# Wait for backend to be ready
kubectl wait --for=condition=Ready pod -l app=backend -n todo-app --timeout=300s

# Check backend is running
kubectl get pods -n todo-app
kubectl logs -f deployment/backend -n todo-app
```

**Get backend URL:**
```bash
# Get the external IP (will be your VM's public IP)
kubectl get svc backend -n todo-app

# Your backend will be accessible at:
# http://<YOUR_VM_PUBLIC_IP>:8000
```

**Test backend:**
```bash
curl http://<YOUR_VM_PUBLIC_IP>:8000/health/live
# Should return: {"status":"healthy"}
```

---

## Part 2: Render Setup (Frontend)

### Step 1: Prepare Frontend for Static Export

On your **local machine**, update Next.js config for static export:

**Update `frontend/next.config.ts`:**
```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',  // Enable static export
  trailingSlash: true,
  images: {
    unoptimized: true,  // Required for static export
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
};

export default nextConfig;
```

**Create `.env.production` file:**
```bash
NEXT_PUBLIC_API_URL=http://<YOUR_ORACLE_VM_PUBLIC_IP>:8000
```

### Step 2: Build Static Frontend

```bash
cd frontend

# Install dependencies
npm install

# Build for production (static export)
npm run build

# This creates an 'out' directory with static files
```

### Step 3: Deploy to Render

**Option A: Deploy via Render Dashboard (Easiest)**

1. Go to: https://render.com/
2. **Sign up** (free, no credit card required)
3. **Connect your GitHub account**
4. **Push your code to GitHub**:

```bash
# On local machine
git add .
git commit -m "feat: Configure frontend for static export to Render"
git push origin main
```

5. **Create new Static Site on Render**:
   - Click **"New +"** > **"Static Site"**
   - Connect your GitHub repository
   - Configure:
     - Name: `todo-frontend`
     - Branch: `main`
     - Root Directory: `frontend`
     - Build Command: `npm install && npm run build`
     - Publish Directory: `out`
     - Environment Variables:
       - Key: `NEXT_PUBLIC_API_URL`
       - Value: `http://<YOUR_ORACLE_VM_IP>:8000`

6. Click **"Create Static Site"**
7. Wait 3-5 minutes for deployment
8. **Your frontend URL**: `https://todo-frontend-xxxx.onrender.com`

**Option B: Deploy via Render CLI**

```bash
# Install Render CLI
npm install -g @render/cli

# Login to Render
render login

# Create render.yaml in frontend directory
cat > render.yaml << 'EOF'
services:
  - type: web
    name: todo-frontend
    env: static
    buildCommand: npm install && npm run build
    staticPublishPath: ./out
    envVars:
      - key: NEXT_PUBLIC_API_URL
        value: http://<YOUR_ORACLE_VM_IP>:8000
EOF

# Deploy
render deploy
```

### Step 4: Update CORS on Backend

Now that you have your Render frontend URL, update backend CORS:

On **Oracle Cloud VM**:

```bash
# Edit backend configmap
kubectl edit configmap backend-config -n todo-app

# Update CORS_ORIGINS to:
# CORS_ORIGINS: "https://todo-frontend-xxxx.onrender.com,https://*.onrender.com"

# Restart backend to apply changes
kubectl rollout restart deployment/backend -n todo-app
```

---

## Part 3: Final Configuration

### Step 1: Test the Deployment

**Test Backend:**
```bash
curl http://<YOUR_ORACLE_VM_IP>:8000/health/live
curl http://<YOUR_ORACLE_VM_IP>:8000/api/docs
```

**Test Frontend:**
1. Open: `https://todo-frontend-xxxx.onrender.com`
2. Register a new user
3. Create a task
4. Verify it saves to database

### Step 2: Set Up Custom Domain (Optional)

**For Backend (Oracle Cloud):**
1. Buy a domain (Namecheap, GoDaddy, Cloudflare)
2. Add A record pointing to Oracle VM IP
3. Set up Nginx reverse proxy on VM for HTTPS

**For Frontend (Render):**
1. Go to Render Dashboard > Settings > Custom Domains
2. Add your domain
3. Update DNS CNAME record as instructed

---

## 📊 Architecture Diagram

```
User Browser
    |
    | HTTPS
    v
[Render CDN] ─────────► Frontend (Static)
    |                      (Next.js)
    | API Calls
    | HTTP
    v
[Oracle Cloud VM] ────► Backend (FastAPI)
    |                      (K3s Pod)
    | PostgreSQL
    v
[PostgreSQL] ─────────► Database
    (K3s Pod)               (Persistent)
```

---

## 💰 Cost Breakdown

| Component | Platform | Cost |
|-----------|----------|------|
| Frontend | Render Static Site | **$0/month** |
| Backend | Oracle Cloud VM | **$0/month** |
| Database | Oracle Cloud (same VM) | **$0/month** |
| Kubernetes | K3s (included) | **$0/month** |
| **TOTAL** | | **$0/month FOREVER** ✅ |

---

## 🔧 Management Commands

### Backend (Oracle Cloud VM)

```bash
# SSH to VM
ssh -i "path/to/key.pem" ubuntu@<VM_IP>

# View pods
kubectl get pods -n todo-app

# View logs
kubectl logs -f deployment/backend -n todo-app
kubectl logs -f deployment/postgres -n todo-app

# Restart backend
kubectl rollout restart deployment/backend -n todo-app

# Scale backend
kubectl scale deployment backend --replicas=3 -n todo-app

# Update backend image
kubectl set image deployment/backend backend=yourusername/todo-backend:v1.0.1 -n todo-app
```

### Frontend (Render)

```bash
# Trigger redeploy (via dashboard or)
render deploy

# View logs (via dashboard)
# Render Dashboard > todo-frontend > Logs
```

---

## 🐛 Troubleshooting

### Backend Not Accessible

```bash
# Check if pods are running
kubectl get pods -n todo-app

# Check logs
kubectl logs deployment/backend -n todo-app

# Check service
kubectl get svc backend -n todo-app

# Test from within VM
curl http://localhost:8000/health/live
```

### Frontend Can't Connect to Backend

1. Check CORS settings in backend
2. Verify API URL in frontend env vars
3. Check firewall rules in Oracle Cloud (port 8000 open)
4. Test backend directly: `curl http://<VM_IP>:8000/health/live`

### Database Connection Issues

```bash
# Check postgres pod
kubectl get pods -n todo-app -l app=postgres

# Check postgres logs
kubectl logs deployment/postgres -n todo-app

# Connect to postgres
kubectl exec -it deployment/postgres -n todo-app -- psql -U todo -d todo_db

# List tables
\dt
```

---

## 🎯 Phase V Checklist

- [ ] Oracle Cloud account created
- [ ] Ampere A1 VM created (4 cores, 24GB RAM)
- [ ] Security list rules configured
- [ ] SSH access working
- [ ] K3s installed on VM
- [ ] PostgreSQL deployed to K3s
- [ ] Backend image pushed to Docker Hub
- [ ] Backend deployed to K3s
- [ ] Backend accessible at VM IP:8000
- [ ] Render account created
- [ ] Frontend configured for static export
- [ ] Frontend deployed to Render
- [ ] CORS configured on backend
- [ ] Frontend can connect to backend
- [ ] Full end-to-end test successful

---

## 🚀 Next Steps After Deployment

1. **Add HTTPS**: Set up Cloudflare or Let's Encrypt
2. **Custom Domain**: Configure your own domain
3. **Monitoring**: Set up Uptime monitoring
4. **Backups**: Configure PostgreSQL backups
5. **CI/CD**: Set up automated deployments

---

## 📝 Summary

You now have a **completely free, production-ready** deployment:

✅ **Frontend**: Fast CDN delivery (Render)
✅ **Backend**: Powerful VM with 24GB RAM (Oracle Cloud)
✅ **Database**: Persistent PostgreSQL (Oracle Cloud)
✅ **Kubernetes**: Full K3s cluster (Oracle Cloud)
✅ **Cost**: $0/month forever

**No credit card charges, no expiry, completely free!** 🎉

---

Ready to start? Let's begin with creating your Oracle Cloud account! 🚀
