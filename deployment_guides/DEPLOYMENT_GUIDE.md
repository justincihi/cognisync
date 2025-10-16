# ThinkSync™ Enhanced Edition - Deployment Guide

## 🚀 **Production Deployment Options**

### **Option 1: Google Cloud Platform (Recommended)**

#### **Prerequisites**
- Google Cloud account with billing enabled
- Google Cloud SDK installed
- OpenAI API key
- Gemini API service account credentials

#### **Step-by-Step Deployment**

1. **Setup Google Cloud Project**
```bash
# Create new project
gcloud projects create thinksync-production --name="ThinkSync Production"

# Set project
gcloud config set project thinksync-production

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

2. **Configure Secrets**
```bash
# Store OpenAI API key
echo "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-

# Store Gemini credentials
gcloud secrets create gemini-credentials --data-file=path/to/credentials.json
```

3. **Deploy to Cloud Run**
```bash
# Deploy application
gcloud run deploy thinksync-enhanced \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars="OPENAI_API_KEY=projects/thinksync-production/secrets/openai-api-key/versions/latest" \
  --set-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/secrets/gemini-credentials.json"
```

4. **Configure Custom Domain (Optional)**
```bash
# Map custom domain
gcloud run domain-mappings create --service thinksync-enhanced --domain your-domain.com
```

#### **Expected Costs**
- **Free Tier**: 2 million requests/month
- **Production**: $0.40 per million requests
- **Typical Monthly Cost**: $10-50 for moderate usage

---

### **Option 2: Heroku**

#### **Prerequisites**
- Heroku account
- Heroku CLI installed
- Git repository

#### **Deployment Steps**

1. **Create Heroku App**
```bash
# Login to Heroku
heroku login

# Create application
heroku create thinksync-enhanced-prod

# Add PostgreSQL addon (optional)
heroku addons:create heroku-postgresql:hobby-dev
```

2. **Configure Environment Variables**
```bash
# Set API keys
heroku config:set OPENAI_API_KEY="your-openai-api-key"
heroku config:set GOOGLE_APPLICATION_CREDENTIALS="$(cat path/to/credentials.json)"
heroku config:set SECRET_KEY="your-secret-key"
```

3. **Deploy Application**
```bash
# Initialize git repository
git init
git add .
git commit -m "Initial ThinkSync deployment"

# Add Heroku remote
heroku git:remote -a thinksync-enhanced-prod

# Deploy
git push heroku main
```

4. **Scale Application**
```bash
# Scale web dynos
heroku ps:scale web=2

# View logs
heroku logs --tail
```

#### **Expected Costs**
- **Free Tier**: 550-1000 dyno hours/month
- **Hobby**: $7/month per dyno
- **Production**: $25-50/month for standard setup

---

### **Option 3: AWS Elastic Beanstalk**

#### **Prerequisites**
- AWS account
- EB CLI installed
- AWS credentials configured

#### **Deployment Steps**

1. **Initialize Elastic Beanstalk**
```bash
# Initialize EB application
eb init thinksync-enhanced

# Select Python platform
# Choose region (us-east-1 recommended)
```

2. **Create Environment**
```bash
# Create production environment
eb create production

# Set environment variables
eb setenv OPENAI_API_KEY="your-openai-api-key"
eb setenv GOOGLE_APPLICATION_CREDENTIALS="credentials.json"
eb setenv SECRET_KEY="your-secret-key"
```

3. **Deploy Application**
```bash
# Deploy current version
eb deploy

# Open application
eb open
```

4. **Configure Auto Scaling**
```bash
# Configure scaling
eb config

# Set min/max instances in configuration
```

#### **Expected Costs**
- **t3.micro**: $8-15/month
- **t3.small**: $15-30/month
- **Load balancer**: $20/month (if needed)

---

### **Option 4: Docker Deployment**

#### **Create Dockerfile**
```dockerfile
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

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/api/health || exit 1

# Run application
CMD ["python", "app.py"]
```

#### **Docker Compose**
```yaml
version: '3.8'

services:
  thinksync:
    build: .
    ports:
      - "5000:5000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./data:/app/data
      - ./credentials.json:/app/credentials.json:ro
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - thinksync
    restart: unless-stopped
```

#### **Deploy with Docker**
```bash
# Build image
docker build -t thinksync-enhanced .

# Run container
docker run -d \
  --name thinksync-prod \
  -p 5000:5000 \
  -e OPENAI_API_KEY="your-key" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/app/credentials.json" \
  -v $(pwd)/credentials.json:/app/credentials.json:ro \
  thinksync-enhanced

# Or use docker-compose
docker-compose up -d
```

---

### **Option 5: DigitalOcean App Platform**

#### **Deployment Steps**

1. **Create App**
```bash
# Install doctl
# Create app spec
cat > app.yaml << EOF
name: thinksync-enhanced
services:
- name: web
  source_dir: /
  github:
    repo: your-username/thinksync-enhanced
    branch: main
  run_command: python app.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: OPENAI_API_KEY
    value: your-openai-api-key
    type: SECRET
  - key: SECRET_KEY
    value: your-secret-key
    type: SECRET
  http_port: 5000
EOF

# Deploy app
doctl apps create --spec app.yaml
```

#### **Expected Costs**
- **Basic**: $5/month
- **Professional**: $12/month
- **Includes**: SSL, CDN, monitoring

---

## 🔧 **Environment Configuration**

### **Required Environment Variables**
```bash
# API Keys
OPENAI_API_KEY=your-openai-api-key
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# Application Settings
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///thinksync.db
PORT=5000

# Optional Settings
DEBUG=False
LOG_LEVEL=INFO
MAX_CONTENT_LENGTH=104857600  # 100MB
```

### **Production Settings**
```python
# app.py production configuration
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = False
    TESTING = False
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///thinksync.db')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # Security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block'
    }
```

---

## 🔐 **Security Configuration**

### **SSL/TLS Setup**
```bash
# Let's Encrypt with Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### **Nginx Configuration**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # File upload size
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📊 **Monitoring & Logging**

### **Application Monitoring**
```python
# Add to app.py
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/thinksync.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('ThinkSync startup')
```

### **Health Checks**
```python
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })
```

---

## 🚀 **Performance Optimization**

### **Database Optimization**
```python
# Add database connection pooling
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('thinksync.db', timeout=20)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```

### **Caching**
```python
# Add Flask-Caching
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/therapy/sessions')
@cache.cached(timeout=300)  # 5 minutes
def list_sessions():
    # Implementation
```

---

## 🔄 **Backup & Recovery**

### **Database Backup**
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 thinksync.db ".backup /backups/thinksync_$DATE.db"

# Keep only last 30 days
find /backups -name "thinksync_*.db" -mtime +30 -delete
```

### **Automated Backups**
```bash
# Add to crontab
0 2 * * * /path/to/backup.sh
```

---

## 📋 **Deployment Checklist**

### **Pre-Deployment**
- [ ] Environment variables configured
- [ ] API keys tested and valid
- [ ] Database schema created
- [ ] SSL certificates installed
- [ ] Domain DNS configured
- [ ] Backup strategy implemented

### **Post-Deployment**
- [ ] Health check endpoint responding
- [ ] Admin login working
- [ ] User registration functional
- [ ] File upload tested
- [ ] Neural simulation working
- [ ] Export functionality tested
- [ ] Monitoring configured
- [ ] Logs accessible

### **Security Verification**
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] File upload restrictions in place
- [ ] Authentication working
- [ ] Session management secure
- [ ] Database access restricted

---

**ThinkSync™ Enhanced Edition** - Production Deployment Guide  
*For additional support, refer to platform-specific documentation and troubleshooting guides.*

