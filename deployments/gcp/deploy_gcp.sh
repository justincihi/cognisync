#!/bin/bash

# CogniSync™ - Google Cloud Platform Deployment Script
# This script deploys CogniSync to GCP App Engine with HIPAA compliance

set -e

echo "🚀 CogniSync™ - Google Cloud Deployment"
echo "========================================"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "❌ Error: Not logged in to gcloud"
    echo "Run: gcloud auth login"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No GCP project selected"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Project: $PROJECT_ID"
echo ""

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable appengine.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudkms.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com

echo "✅ APIs enabled"
echo ""

# Create App Engine app if it doesn't exist
if ! gcloud app describe &> /dev/null; then
    echo "🏗️  Creating App Engine application..."
    echo "Select a region (us-central recommended for HIPAA):"
    gcloud app create
    echo "✅ App Engine created"
else
    echo "✅ App Engine already exists"
fi

echo ""

# Create Secret Manager secrets
echo "🔐 Setting up Secret Manager..."

# Function to create or update secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if gcloud secrets describe $secret_name --project=$PROJECT_ID &> /dev/null; then
        echo "  Updating secret: $secret_name"
        echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=-
    else
        echo "  Creating secret: $secret_name"
        echo -n "$secret_value" | gcloud secrets create $secret_name --data-file=- --replication-policy="automatic"
    fi
}

# Generate encryption keys if not provided
if [ -z "$DB_ENCRYPTION_KEY" ]; then
    echo "  Generating DB encryption key..."
    DB_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
fi

if [ -z "$FILE_ENCRYPTION_KEY" ]; then
    echo "  Generating file encryption key..."
    FILE_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
fi

# Create secrets
create_or_update_secret "db-encryption-key" "$DB_ENCRYPTION_KEY"
create_or_update_secret "file-encryption-key" "$FILE_ENCRYPTION_KEY"

# Create secrets for API keys (you'll need to set these manually)
if [ -n "$OPENAI_API_KEY" ]; then
    create_or_update_secret "openai-api-key" "$OPENAI_API_KEY"
else
    echo "  ⚠️  OPENAI_API_KEY not set - create manually in Secret Manager"
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
    create_or_update_secret "anthropic-api-key" "$ANTHROPIC_API_KEY"
else
    echo "  ⚠️  ANTHROPIC_API_KEY not set - create manually in Secret Manager"
fi

echo "✅ Secrets configured"
echo ""

# Create Cloud Storage bucket for file storage
BUCKET_NAME="${PROJECT_ID}-cognisync-files"
echo "📦 Creating Cloud Storage bucket: $BUCKET_NAME"

if ! gsutil ls -b gs://$BUCKET_NAME &> /dev/null; then
    gsutil mb -p $PROJECT_ID -c STANDARD -l us-central1 gs://$BUCKET_NAME
    
    # Enable encryption
    gsutil encryption set -k projects/$PROJECT_ID/locations/us-central1/keyRings/cognisync/cryptoKeys/storage-key gs://$BUCKET_NAME
    
    # Set lifecycle policy (7 year retention)
    cat > /tmp/lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 2555}
      }
    ]
  }
}
EOF
    gsutil lifecycle set /tmp/lifecycle.json gs://$BUCKET_NAME
    rm /tmp/lifecycle.json
    
    echo "✅ Bucket created with encryption and retention policy"
else
    echo "✅ Bucket already exists"
fi

echo ""

# Create Cloud SQL instance (optional, for production)
read -p "Do you want to create a Cloud SQL PostgreSQL instance? (recommended for production) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    INSTANCE_NAME="cognisync-db"
    echo "🗄️  Creating Cloud SQL instance: $INSTANCE_NAME"
    
    gcloud sql instances create $INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=us-central1 \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase \
        --backup \
        --backup-start-time=03:00 \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=04 \
        --database-flags=cloudsql.enable_pgaudit=on
    
    # Create database
    gcloud sql databases create cognisync --instance=$INSTANCE_NAME
    
    # Create user
    DB_PASSWORD=$(openssl rand -base64 32)
    gcloud sql users create cognisync-user \
        --instance=$INSTANCE_NAME \
        --password=$DB_PASSWORD
    
    # Store password in Secret Manager
    create_or_update_secret "db-password" "$DB_PASSWORD"
    
    echo "✅ Cloud SQL instance created"
    echo "  Connection name: $PROJECT_ID:us-central1:$INSTANCE_NAME"
fi

echo ""

# Deploy application
echo "🚀 Deploying application to App Engine..."
gcloud app deploy app.yaml --quiet

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Configure API keys in Secret Manager if not already done"
echo "2. Set up Cloud Armor for DDoS protection"
echo "3. Configure Cloud Logging and Monitoring"
echo "4. Enable VPC Service Controls for additional security"
echo "5. Complete HIPAA compliance checklist"
echo ""
echo "🌐 Your application is available at:"
gcloud app browse --no-launch-browser

echo ""
echo "📚 See README_GCP.md for detailed configuration and HIPAA compliance steps"

