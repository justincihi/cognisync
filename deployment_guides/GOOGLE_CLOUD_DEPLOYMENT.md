# ThinkSync™ Google Cloud Platform Deployment Guide

## 🚀 **Google Cloud Platform Deployment Options**

### Option 1: Google Cloud Run (Recommended)
**Best for**: Serverless, auto-scaling, cost-effective deployment

### Option 2: Google App Engine
**Best for**: Managed platform with automatic scaling

### Option 3: Google Compute Engine
**Best for**: Full control over server configuration

---

## 🎯 **Option 1: Google Cloud Run Deployment (Recommended)**

### Prerequisites
```bash
# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

### Step 1: Project Setup
```bash
# Create new project or select existing
gcloud projects create thinksync-production --name="ThinkSync Production"
gcloud config set project thinksync-production

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Step 2: Prepare Application for Cloud Run

#### Create Dockerfile for Backend
```dockerfile
# Create: backend/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app

# Start command
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 src.main:app
```

#### Update requirements.txt for Cloud Run
```txt
# Add to backend/requirements.txt
gunicorn==21.2.0
```

#### Update main.py for Cloud Run
```python
# Add to backend/src/main.py
import os

# ... existing code ...

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
```

### Step 3: Deploy Backend to Cloud Run
```bash
# Navigate to backend directory
cd backend

# Build and deploy
gcloud run deploy thinksync-backend \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars OPENAI_API_KEY="your_openai_api_key" \
    --set-env-vars OPENAI_API_BASE="https://api.openai.com/v1" \
    --set-env-vars GOOGLE_APPLICATION_CREDENTIALS="/app/credentials.json" \
    --memory 2Gi \
    --cpu 2 \
    --timeout 900 \
    --max-instances 10

# Note the service URL (e.g., https://thinksync-backend-xxx-uc.a.run.app)
```

### Step 4: Upload Gemini Credentials
```bash
# Create secret for Gemini credentials
gcloud secrets create gemini-credentials \
    --data-file=logical-matrix-460704-b1-f04b8677292f.json

# Update Cloud Run service to use secret
gcloud run services update thinksync-backend \
    --region us-central1 \
    --update-secrets GOOGLE_APPLICATION_CREDENTIALS=gemini-credentials:latest
```

### Step 5: Deploy Frontend to Firebase Hosting
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize Firebase in frontend directory
cd frontend
firebase init hosting

# Select your project or create new one
# Choose dist/ as public directory
# Configure as single-page app: Yes
# Don't overwrite index.html

# Update API endpoint in frontend
# Edit src/App.jsx to use your Cloud Run backend URL
const API_BASE_URL = 'https://thinksync-backend-xxx-uc.a.run.app';

# Rebuild frontend
npm run build

# Deploy to Firebase
firebase deploy
```

---

## 🎯 **Option 2: Google App Engine Deployment**

### Step 1: Prepare app.yaml
```yaml
# Create: backend/app.yaml
runtime: python311

env_variables:
  OPENAI_API_KEY: "your_openai_api_key"
  OPENAI_API_BASE: "https://api.openai.com/v1"
  GOOGLE_APPLICATION_CREDENTIALS: "logical-matrix-460704-b1-f04b8677292f.json"

automatic_scaling:
  min_instances: 0
  max_instances: 10
  target_cpu_utilization: 0.6

resources:
  cpu: 2
  memory_gb: 4
  disk_size_gb: 10

handlers:
- url: /static
  static_dir: static
  
- url: /.*
  script: auto
  secure: always
```

### Step 2: Deploy to App Engine
```bash
# Navigate to backend directory
cd backend

# Copy Gemini credentials
cp ../logical-matrix-460704-b1-f04b8677292f.json .

# Deploy
gcloud app deploy app.yaml

# Get the URL
gcloud app browse
```

---

## 🎯 **Option 3: Google Compute Engine Deployment**

### Step 1: Create VM Instance
```bash
# Create VM with sufficient resources
gcloud compute instances create thinksync-vm \
    --zone=us-central1-a \
    --machine-type=e2-standard-4 \
    --boot-disk-size=50GB \
    --boot-disk-type=pd-standard \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --tags=http-server,https-server

# Configure firewall
gcloud compute firewall-rules create allow-thinksync \
    --allow tcp:80,tcp:443,tcp:3000 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server
```

### Step 2: Setup Application on VM
```bash
# SSH into VM
gcloud compute ssh thinksync-vm --zone=us-central1-a

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.11 python3-pip nodejs npm nginx -y

# Upload ThinkSync files (use gcloud scp or git clone)
gcloud compute scp --recurse thinksync_export/ thinksync-vm:~/ --zone=us-central1-a

# Setup backend
cd thinksync_export/backend
pip3 install -r requirements.txt

# Setup environment variables
export OPENAI_API_KEY="your_openai_api_key"
export OPENAI_API_BASE="https://api.openai.com/v1"
export GOOGLE_APPLICATION_CREDENTIALS="/home/user/logical-matrix-460704-b1-f04b8677292f.json"

# Install PM2 for process management
sudo npm install -g pm2

# Start backend with PM2
pm2 start src/main.py --name thinksync-backend --interpreter python3

# Setup Nginx for frontend
sudo cp frontend/dist/* /var/www/html/
sudo systemctl restart nginx
```

---

## 🔧 **Configuration & Security**

### Environment Variables Setup
```bash
# For Cloud Run
gcloud run services update thinksync-backend \
    --set-env-vars OPENAI_API_KEY="sk-..." \
    --set-env-vars OPENAI_API_BASE="https://api.openai.com/v1" \
    --region us-central1

# For App Engine (in app.yaml)
env_variables:
  OPENAI_API_KEY: "sk-..."
  OPENAI_API_BASE: "https://api.openai.com/v1"
```

### SSL/HTTPS Configuration
```bash
# Cloud Run and App Engine automatically provide HTTPS
# For Compute Engine, use Let's Encrypt:
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

### Custom Domain Setup
```bash
# For Cloud Run
gcloud run domain-mappings create \
    --service thinksync-backend \
    --domain api.yourdomain.com \
    --region us-central1

# For Firebase Hosting
firebase hosting:channel:deploy production --only hosting
```

---

## 📊 **Monitoring & Logging**

### Enable Cloud Monitoring
```bash
# Enable monitoring APIs
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com

# View logs
gcloud logs read "resource.type=cloud_run_revision" --limit 50
```

### Performance Monitoring
```python
# Add to main.py for monitoring
from google.cloud import monitoring_v3

# Create monitoring client
client = monitoring_v3.MetricServiceClient()

# Log custom metrics
@app.before_request
def log_request():
    # Log request metrics
    pass
```

---

## 💰 **Cost Optimization**

### Cloud Run Pricing
- **CPU**: $0.00002400 per vCPU-second
- **Memory**: $0.00000250 per GiB-second
- **Requests**: $0.40 per million requests
- **Free tier**: 2 million requests/month

### Optimization Tips
```yaml
# Optimize Cloud Run configuration
resources:
  limits:
    cpu: "1"
    memory: "1Gi"
  
concurrency: 80
timeout: 300s
```

---

## 🧪 **Testing Deployment**

### Health Check
```bash
# Test Cloud Run deployment
curl https://thinksync-backend-xxx-uc.a.run.app/api/therapy/test

# Test file upload
curl -X POST https://thinksync-backend-xxx-uc.a.run.app/api/therapy/sessions \
  -F "audio_file=@BHAudioOnly.m4a" \
  -F "client_name=BH-F23" \
  -F "therapy_type=CBT" \
  -F "summary_format=SOAP"
```

### Load Testing
```bash
# Install Apache Bench
sudo apt install apache2-utils -y

# Test API performance
ab -n 100 -c 10 https://your-cloud-run-url/api/therapy/test
```

---

## 🔒 **Security Best Practices**

### IAM Configuration
```bash
# Create service account for application
gcloud iam service-accounts create thinksync-app \
    --display-name="ThinkSync Application"

# Grant necessary permissions
gcloud projects add-iam-policy-binding thinksync-production \
    --member="serviceAccount:thinksync-app@thinksync-production.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

### Secret Management
```bash
# Store sensitive data in Secret Manager
gcloud secrets create openai-api-key --data-file=-
# Enter your API key when prompted

# Use in Cloud Run
gcloud run services update thinksync-backend \
    --update-secrets OPENAI_API_KEY=openai-api-key:latest
```

---

## 📞 **Support & Troubleshooting**

### Common Issues
1. **Memory errors**: Increase memory allocation in Cloud Run
2. **Timeout errors**: Increase timeout to 900s for large files
3. **CORS issues**: Ensure proper CORS configuration in Flask app

### Debugging
```bash
# View Cloud Run logs
gcloud logs tail "resource.type=cloud_run_revision"

# Check service status
gcloud run services describe thinksync-backend --region us-central1
```

This comprehensive guide provides multiple Google Cloud deployment options for ThinkSync™, with Cloud Run being the recommended approach for its scalability and cost-effectiveness.

