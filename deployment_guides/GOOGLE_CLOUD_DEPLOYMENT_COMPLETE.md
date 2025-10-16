# ThinkSync™ Enhanced Edition - Complete Google Cloud Deployment Guide

## 🎯 **Step-by-Step Google Cloud Platform Deployment**

### **Prerequisites**
- Google Cloud account with billing enabled
- Google Cloud SDK installed on your computer
- ThinkSync™ Enhanced Edition package extracted

---

## 📋 **Step 1: Install Google Cloud SDK**

### **For Windows:**
1. Download Google Cloud SDK from: https://cloud.google.com/sdk/docs/install
2. Run the installer and follow the setup wizard
3. Open Command Prompt or PowerShell

### **For Mac:**
```bash
# Install using Homebrew
brew install --cask google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

### **For Linux:**
```bash
# Add Google Cloud SDK repository
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

# Import Google Cloud public key
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

# Install SDK
sudo apt-get update && sudo apt-get install google-cloud-cli
```

---

## 📋 **Step 2: Initialize Google Cloud**

```bash
# Login to Google Cloud
gcloud auth login

# Initialize gcloud (this will open a browser)
gcloud init

# Follow the prompts to:
# 1. Select or create a Google Cloud project
# 2. Choose a default region (us-central1 recommended)
```

---

## 📋 **Step 3: Create Google Cloud Project**

```bash
# Create a new project (replace PROJECT_ID with your desired project name)
gcloud projects create thinksync-production --name="ThinkSync Production"

# Set the project as default
gcloud config set project thinksync-production

# Enable billing (required for Cloud Run)
# Go to: https://console.cloud.google.com/billing
# Link your project to a billing account
```

---

## 📋 **Step 4: Enable Required APIs**

```bash
# Enable Cloud Run API
gcloud services enable run.googleapis.com

# Enable Cloud Build API (for building containers)
gcloud services enable cloudbuild.googleapis.com

# Enable Secret Manager API (for storing API keys)
gcloud services enable secretmanager.googleapis.com

# Enable Container Registry API
gcloud services enable containerregistry.googleapis.com
```

---

## 📋 **Step 5: Prepare ThinkSync™ Files**

### **Extract and Navigate to Package**
```bash
# Extract the ThinkSync package
tar -xzf ThinkSync_Enhanced_Complete_20250913_222328.tar.gz

# Navigate to the deployment directory
cd ThinkSync_Final_Deployment
```

### **Create Additional Google Cloud Files**

#### **Create `app.yaml` for App Engine (Alternative Option)**
```yaml
# app.yaml
runtime: python311

env_variables:
  OPENAI_API_KEY: "your-openai-api-key-here"
  SECRET_KEY: "your-secret-key-here"

automatic_scaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 0.6

resources:
  cpu: 1
  memory_gb: 2
  disk_size_gb: 10
```

#### **Create `Dockerfile` for Cloud Run**
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Set environment variable for port
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/api/health || exit 1

# Run application
CMD ["python", "app.py"]
```

#### **Create `.gcloudignore`**
```
# .gcloudignore
.git
.gitignore
README.md
DEPLOYMENT_GUIDE.md
*.md
venv/
__pycache__/
*.pyc
.env
.DS_Store
node_modules/
```

#### **Update `app.py` for Google Cloud**
```python
# Add this to the end of app.py, replacing the existing if __name__ == '__main__': block

if __name__ == '__main__':
    print("🚀 ThinkSync™ Enhanced Edition - Google Cloud Production")
    print("=" * 60)
    print("✅ Features Available:")
    print("• Complete User Authentication & Authorization")
    print("• Advanced Sentiment Analysis Integration")
    print("• Session Management & Persistence")
    print("• SOAP/BIRP Clinical Documentation")
    print("• Multi-format Export Capabilities")
    print("• Admin Dashboard & User Management")
    print()
    print("🎯 Admin Access:")
    print("• Username: admin@thinksync.com")
    print("• Password: 3942-granite-35")
    print()
    print("🚀 Ready for Google Cloud production!")
    
    # Get port from environment variable (Google Cloud sets this)
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    app.run(host='0.0.0.0', port=port, debug=False)
```

---

## 📋 **Step 6: Store API Keys in Secret Manager**

```bash
# Store OpenAI API key
echo "your-openai-api-key-here" | gcloud secrets create openai-api-key --data-file=-

# Store your secret key
echo "your-secret-key-here" | gcloud secrets create app-secret-key --data-file=-

# If you have Gemini credentials file
gcloud secrets create gemini-credentials --data-file=path/to/your/gemini-credentials.json

# Verify secrets were created
gcloud secrets list
```

---

## 📋 **Step 7: Deploy to Google Cloud Run (Recommended)**

### **Option A: Deploy with gcloud command**
```bash
# Deploy to Cloud Run
gcloud run deploy thinksync-enhanced \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --port 8080 \
  --set-env-vars="OPENAI_API_KEY=projects/thinksync-production/secrets/openai-api-key/versions/latest" \
  --set-env-vars="SECRET_KEY=projects/thinksync-production/secrets/app-secret-key/versions/latest"
```

### **Option B: Deploy with Cloud Build**
```bash
# Create cloudbuild.yaml
cat > cloudbuild.yaml << 'EOF'
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/thinksync-enhanced', '.']
  
  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/thinksync-enhanced']
  
  # Deploy container image to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
    - 'run'
    - 'deploy'
    - 'thinksync-enhanced'
    - '--image'
    - 'gcr.io/$PROJECT_ID/thinksync-enhanced'
    - '--region'
    - 'us-central1'
    - '--platform'
    - 'managed'
    - '--allow-unauthenticated'
    - '--memory'
    - '2Gi'
    - '--cpu'
    - '2'

images:
  - 'gcr.io/$PROJECT_ID/thinksync-enhanced'
EOF

# Submit build
gcloud builds submit --config cloudbuild.yaml .
```

---

## 📋 **Step 8: Alternative - Deploy to App Engine**

```bash
# Create app.yaml (if not already created)
cat > app.yaml << 'EOF'
runtime: python311

env_variables:
  OPENAI_API_KEY: "your-openai-api-key-here"
  SECRET_KEY: "your-secret-key-here"

automatic_scaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 0.6

resources:
  cpu: 1
  memory_gb: 2
  disk_size_gb: 10
EOF

# Deploy to App Engine
gcloud app deploy

# View your application
gcloud app browse
```

---

## 📋 **Step 9: Configure Custom Domain (Optional)**

```bash
# Map custom domain to Cloud Run
gcloud run domain-mappings create \
  --service thinksync-enhanced \
  --domain your-domain.com \
  --region us-central1

# For App Engine
gcloud app domain-mappings create your-domain.com
```

---

## 📋 **Step 10: Set Up SSL Certificate**

### **For Cloud Run with Custom Domain:**
```bash
# Google automatically provisions SSL certificates for custom domains
# No additional configuration needed

# Verify SSL certificate
curl -I https://your-domain.com
```

### **For App Engine:**
```bash
# SSL certificates are automatically managed
# Verify at: https://console.cloud.google.com/appengine/settings/certificates
```

---

## 📋 **Step 11: Test Your Deployment**

```bash
# Get the service URL
gcloud run services describe thinksync-enhanced --region us-central1 --format 'value(status.url)'

# Test health endpoint
curl https://your-service-url/api/health

# Test admin login
# Navigate to: https://your-service-url/admin
# Username: admin@thinksync.com
# Password: 3942-granite-35
```

---

## 📋 **Step 12: Monitor and Maintain**

### **View Logs:**
```bash
# View Cloud Run logs
gcloud logs read --service thinksync-enhanced --region us-central1

# Stream live logs
gcloud logs tail --service thinksync-enhanced --region us-central1
```

### **Update Deployment:**
```bash
# Redeploy with changes
gcloud run deploy thinksync-enhanced \
  --source . \
  --platform managed \
  --region us-central1
```

### **Scale Service:**
```bash
# Update scaling settings
gcloud run services update thinksync-enhanced \
  --region us-central1 \
  --min-instances 2 \
  --max-instances 20
```

---

## 💰 **Cost Estimation**

### **Cloud Run Pricing:**
- **Free Tier**: 2 million requests/month, 360,000 GB-seconds/month
- **After Free Tier**: 
  - $0.40 per million requests
  - $0.00002400 per GB-second
  - $0.00000900 per vCPU-second

### **Typical Monthly Costs:**
- **Light Usage** (< 100 sessions/month): **FREE**
- **Moderate Usage** (500 sessions/month): **$5-15**
- **Heavy Usage** (2000+ sessions/month): **$20-50**

### **App Engine Pricing:**
- **Free Tier**: 28 instance hours/day
- **Standard Environment**: $0.05-0.10 per instance hour

---

## 🔧 **Troubleshooting**

### **Common Issues:**

#### **Build Fails:**
```bash
# Check build logs
gcloud builds log [BUILD_ID]

# Common fix: Update requirements.txt
pip freeze > requirements.txt
```

#### **Service Won't Start:**
```bash
# Check service logs
gcloud logs read --service thinksync-enhanced --region us-central1 --limit 50

# Common fix: Check port configuration
# Ensure app.py uses PORT environment variable
```

#### **Database Issues:**
```bash
# For production, consider Cloud SQL instead of SQLite
gcloud sql instances create thinksync-db \
  --database-version POSTGRES_13 \
  --tier db-f1-micro \
  --region us-central1
```

#### **API Key Issues:**
```bash
# Verify secrets
gcloud secrets versions access latest --secret openai-api-key

# Update secret
echo "new-api-key" | gcloud secrets versions add openai-api-key --data-file=-
```

---

## 📋 **Complete File Checklist**

### **Required Files in Your Directory:**
- ✅ `app.py` - Main Flask application
- ✅ `requirements.txt` - Python dependencies
- ✅ `static/` - Frontend files
- ✅ `Dockerfile` - Container configuration
- ✅ `.gcloudignore` - Files to ignore during deployment
- ✅ `app.yaml` - App Engine configuration (if using App Engine)
- ✅ `cloudbuild.yaml` - Cloud Build configuration (if using Cloud Build)

### **Commands Summary:**
```bash
# 1. Initialize
gcloud init
gcloud projects create thinksync-production
gcloud config set project thinksync-production

# 2. Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com

# 3. Store secrets
echo "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-

# 4. Deploy
gcloud run deploy thinksync-enhanced --source . --platform managed --region us-central1 --allow-unauthenticated

# 5. Test
curl https://your-service-url/api/health
```

---

## 🎉 **Success!**

After following these steps, your ThinkSync™ Enhanced Edition will be live on Google Cloud Platform with:

- ✅ **Public URL**: https://thinksync-enhanced-[hash]-uc.a.run.app
- ✅ **SSL Certificate**: Automatically provisioned
- ✅ **Auto-scaling**: 0 to 10 instances based on traffic
- ✅ **Global CDN**: Fast worldwide access
- ✅ **Monitoring**: Built-in logging and metrics
- ✅ **99.95% Uptime SLA**: Enterprise-grade reliability

**Your ThinkSync™ application is now production-ready on Google Cloud!**

