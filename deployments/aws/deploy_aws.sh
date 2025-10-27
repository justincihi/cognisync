#!/bin/bash

# CogniSync™ - AWS Deployment Script
# This script deploys CogniSync to AWS with HIPAA compliance

set -e

echo "🚀 CogniSync™ - AWS Deployment"
echo "=============================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is not installed"
    echo "Install from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if EB CLI is installed
if ! command -v eb &> /dev/null; then
    echo "❌ Error: Elastic Beanstalk CLI is not installed"
    echo "Install: pip install awsebcli"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
fi

echo "✅ AWS CLI configured"
echo ""

# Set variables
APP_NAME="cognisync"
ENV_NAME="cognisync-prod"
REGION="us-east-1"  # Change as needed
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "📋 Configuration:"
echo "  Application: $APP_NAME"
echo "  Environment: $ENV_NAME"
echo "  Region: $REGION"
echo "  Account: $ACCOUNT_ID"
echo ""

# Create KMS key for encryption
echo "🔐 Creating KMS encryption key..."
KMS_KEY_ID=$(aws kms create-key \
    --description "CogniSync HIPAA encryption key" \
    --key-policy file://<(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Enable IAM User Permissions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${ACCOUNT_ID}:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    }
  ]
}
EOF
) \
    --query 'KeyMetadata.KeyId' \
    --output text 2>/dev/null || echo "")

if [ -n "$KMS_KEY_ID" ]; then
    echo "✅ KMS key created: $KMS_KEY_ID"
    
    # Create alias
    aws kms create-alias \
        --alias-name alias/cognisync-hipaa \
        --target-key-id $KMS_KEY_ID 2>/dev/null || echo "  Alias already exists"
else
    echo "  KMS key may already exist, continuing..."
    KMS_KEY_ID=$(aws kms list-aliases --query "Aliases[?AliasName=='alias/cognisync-hipaa'].TargetKeyId" --output text)
fi

echo ""

# Create S3 bucket for encrypted file storage
BUCKET_NAME="cognisync-files-${ACCOUNT_ID}"
echo "📦 Creating S3 bucket: $BUCKET_NAME"

if ! aws s3 ls s3://$BUCKET_NAME &> /dev/null; then
    aws s3 mb s3://$BUCKET_NAME --region $REGION
    
    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket $BUCKET_NAME \
        --server-side-encryption-configuration '{
            "Rules": [{
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "aws:kms",
                    "KMSMasterKeyID": "'$KMS_KEY_ID'"
                }
            }]
        }'
    
    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket $BUCKET_NAME \
        --versioning-configuration Status=Enabled
    
    # Block public access
    aws s3api put-public-access-block \
        --bucket $BUCKET_NAME \
        --public-access-block-configuration \
            "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    
    # Set lifecycle policy (7 year retention)
    aws s3api put-bucket-lifecycle-configuration \
        --bucket $BUCKET_NAME \
        --lifecycle-configuration '{
            "Rules": [{
                "Id": "DeleteAfter7Years",
                "Status": "Enabled",
                "Expiration": {
                    "Days": 2555
                }
            }]
        }'
    
    echo "✅ S3 bucket created with encryption and retention"
else
    echo "✅ S3 bucket already exists"
fi

echo ""

# Create RDS PostgreSQL instance
read -p "Do you want to create an RDS PostgreSQL instance? (recommended for production) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    DB_INSTANCE="cognisync-db"
    DB_NAME="cognisync"
    DB_USER="cognisync_admin"
    DB_PASSWORD=$(openssl rand -base64 32)
    
    echo "🗄️  Creating RDS PostgreSQL instance..."
    
    # Create DB subnet group
    aws rds create-db-subnet-group \
        --db-subnet-group-name cognisync-subnet-group \
        --db-subnet-group-description "CogniSync DB subnet group" \
        --subnet-ids subnet-xxxxx subnet-yyyyy \
        2>/dev/null || echo "  Subnet group may already exist"
    
    # Create RDS instance
    aws rds create-db-instance \
        --db-instance-identifier $DB_INSTANCE \
        --db-instance-class db.t3.micro \
        --engine postgres \
        --engine-version 15.3 \
        --master-username $DB_USER \
        --master-user-password $DB_PASSWORD \
        --allocated-storage 20 \
        --storage-type gp3 \
        --storage-encrypted \
        --kms-key-id $KMS_KEY_ID \
        --backup-retention-period 35 \
        --preferred-backup-window "03:00-04:00" \
        --preferred-maintenance-window "sun:04:00-sun:05:00" \
        --enable-cloudwatch-logs-exports '["postgresql"]' \
        --deletion-protection \
        --no-publicly-accessible
    
    echo "✅ RDS instance creation initiated (this takes 10-15 minutes)"
    echo "  Instance: $DB_INSTANCE"
    echo "  Database: $DB_NAME"
    echo "  Username: $DB_USER"
    echo "  Password stored in Secrets Manager"
    
    # Store credentials in Secrets Manager
    aws secretsmanager create-secret \
        --name cognisync/db-credentials \
        --secret-string "{\"username\":\"$DB_USER\",\"password\":\"$DB_PASSWORD\",\"host\":\"$DB_INSTANCE.xxxxx.$REGION.rds.amazonaws.com\",\"database\":\"$DB_NAME\"}" \
        2>/dev/null || echo "  Secret may already exist"
fi

echo ""

# Create Secrets Manager secrets for encryption keys
echo "🔐 Creating Secrets Manager secrets..."

# Generate encryption keys
DB_ENC_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
FILE_ENC_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

aws secretsmanager create-secret \
    --name cognisync/db-encryption-key \
    --secret-string "$DB_ENC_KEY" \
    2>/dev/null || aws secretsmanager update-secret \
    --secret-id cognisync/db-encryption-key \
    --secret-string "$DB_ENC_KEY"

aws secretsmanager create-secret \
    --name cognisync/file-encryption-key \
    --secret-string "$FILE_ENC_KEY" \
    2>/dev/null || aws secretsmanager update-secret \
    --secret-id cognisync/file-encryption-key \
    --secret-string "$FILE_ENC_KEY"

echo "✅ Encryption keys stored in Secrets Manager"
echo ""

# Initialize Elastic Beanstalk
echo "🏗️  Initializing Elastic Beanstalk..."

if [ ! -f .elasticbeanstalk/config.yml ]; then
    eb init $APP_NAME \
        --platform python-3.11 \
        --region $REGION
else
    echo "  Already initialized"
fi

echo ""

# Create environment
echo "🚀 Creating Elastic Beanstalk environment..."

eb create $ENV_NAME \
    --instance-type t3.small \
    --platform "python-3.11" \
    --envvars \
        USE_REAL_AI=true,\
        SESSION_TIMEOUT_MINUTES=15,\
        DATA_RETENTION_YEARS=7,\
        AWS_S3_BUCKET=$BUCKET_NAME,\
        AWS_REGION=$REGION

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📋 Next steps:"
echo "1. Add API keys to Secrets Manager:"
echo "   aws secretsmanager create-secret --name cognisync/openai-api-key --secret-string 'YOUR_KEY'"
echo "   aws secretsmanager create-secret --name cognisync/anthropic-api-key --secret-string 'YOUR_KEY'"
echo ""
echo "2. Configure IAM roles for Secrets Manager access"
echo "3. Set up CloudWatch alarms and monitoring"
echo "4. Enable AWS WAF for additional security"
echo "5. Configure VPC and security groups"
echo "6. Sign BAA with AWS (required for HIPAA)"
echo ""
echo "🌐 Check deployment status:"
echo "   eb status"
echo "   eb open"
echo ""
echo "📚 See README_AWS.md for detailed HIPAA compliance configuration"

