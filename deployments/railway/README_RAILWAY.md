# CogniSync™ - Railway Deployment Guide

## ⚠️ IMPORTANT HIPAA WARNING

**Railway is NOT HIPAA compliant by default. Use ONLY for:**
- Development and testing
- Demonstrations  
- Non-PHI applications

**For HIPAA compliance on Railway, you must:**
1. Contact Railway sales for Enterprise plan
2. Sign a Business Associate Agreement (BAA)
3. Enable encryption at rest
4. Configure audit logging
5. Implement additional security measures

---

## Quick Start on Railway

### 1. Deploy from GitHub

1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `justincihi/cognisync`
5. Click "Deploy"

### 2. Configure Environment Variables

In Railway dashboard, go to Variables and add:

```
# Required
DB_ENCRYPTION_KEY=<generate_using_command_below>
FILE_ENCRYPTION_KEY=<generate_using_command_below>
OPENAI_API_KEY=<your_openai_key>
ANTHROPIC_API_KEY=<your_anthropic_key>

# Port (Railway provides this automatically)
PORT=8080

# Optional
USE_REAL_AI=true
SESSION_TIMEOUT_MINUTES=15
DATA_RETENTION_YEARS=7
FLASK_ENV=production
```

### 3. Generate Encryption Keys

Run locally or in Railway shell:

```bash
python3 << 'EOF'
from cryptography.fernet import Fernet
print("DB_ENCRYPTION_KEY=" + Fernet.generate_key().decode())
print("FILE_ENCRYPTION_KEY=" + Fernet.generate_key().decode())
EOF
```

### 4. Add Persistent Volume (Important!)

1. In Railway dashboard, go to your service
2. Click "Settings"
3. Scroll to "Volumes"
4. Click "Add Volume"
5. Mount path: `/app/data`
6. Size: 1GB (or more as needed)

This ensures your database and uploaded files persist across deployments.

### 5. Configure Custom Domain (Optional)

1. Go to "Settings"
2. Scroll to "Domains"
3. Click "Generate Domain" for a Railway subdomain
4. Or add your custom domain

---

## File Structure for Railway

```
cognisync/
├── app.py
├── encrypted_db.py
├── file_encryption.py
├── audit_logger.py
├── mfa_auth.py
├── data_retention.py
├── ai_service.py
├── requirements_hipaa.txt
├── railway.json          # Railway configuration
├── Procfile             # Process definition
├── static/
└── data/                # Persistent volume mount
    ├── cognisync_encrypted.db
    └── uploads/
```

### Create Procfile

Create a file named `Procfile` in your repository root:

```
web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 app:app
```

---

## Railway Pricing

### Hobby Plan (Free Trial)
- $5 free credit per month
- Good for development/testing
- Sleeps after inactivity

### Developer Plan ($5/month)
- $5 credit included
- No sleeping
- Better for demos

### Team Plan ($20/month)
- $20 credit included
- Team collaboration
- Priority support

### Enterprise Plan (Custom)
- **Required for HIPAA compliance**
- BAA available
- Dedicated resources
- Enhanced security
- Contact Railway sales

---

## HIPAA Compliance on Railway

### Current Status: ❌ NOT HIPAA Compliant

To make Railway HIPAA compliant:

#### 1. Upgrade to Enterprise Plan
- Contact: enterprise@railway.app
- Request BAA (Business Associate Agreement)
- Discuss HIPAA requirements

#### 2. Enable Required Features
- Encryption at rest for volumes
- Enhanced audit logging
- Dedicated infrastructure
- Network isolation

#### 3. Implement Additional Security
- Use PostgreSQL instead of SQLite
- Enable database encryption
- Configure VPN/private networking
- Set up monitoring and alerts

#### 4. Estimated Cost
- Enterprise plan: $500-2000/month minimum
- Additional resources as needed

---

## Advantages of Railway

### ✅ Pros:

1. **Easy Deployment**: GitHub integration
2. **Automatic HTTPS**: SSL certificates included
3. **Environment Variables**: Easy to manage
4. **Logs**: Built-in log viewer
5. **Metrics**: Resource monitoring
6. **Scaling**: Easy horizontal scaling
7. **Persistent Volumes**: Data persistence

### ❌ Cons:

1. **Not HIPAA by Default**: Requires Enterprise plan
2. **Cost**: Can get expensive with usage
3. **Limited Free Tier**: $5/month credit only
4. **No BAA on Standard Plans**: Enterprise only

---

## Recommended Configuration

### For Development/Demo:

```bash
# .env file
USE_REAL_AI=false  # Use demo mode to save API costs
SESSION_TIMEOUT_MINUTES=30
DATA_RETENTION_YEARS=1  # Shorter for testing
```

### For Production (with Enterprise + BAA):

```bash
# Railway environment variables
USE_REAL_AI=true
SESSION_TIMEOUT_MINUTES=15
DATA_RETENTION_YEARS=7
FLASK_ENV=production
DATABASE_URL=postgresql://...  # Use PostgreSQL
REDIS_URL=redis://...  # For session management
```

---

## Monitoring and Logs

### View Logs:
1. Go to your service in Railway
2. Click "Deployments"
3. Click on latest deployment
4. View logs in real-time

### Monitor Resources:
1. Click "Metrics" tab
2. View CPU, memory, network usage
3. Set up alerts for high usage

---

## Backup Strategy

### Database Backups:

```bash
# Add to your app or use Railway cron
# Backup database daily
python3 << 'EOF'
import shutil
from datetime import datetime

backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
shutil.copy('data/cognisync_encrypted.db', f'data/backups/{backup_name}')
EOF
```

### File Backups:

Consider using:
- AWS S3 for encrypted file backups
- Google Cloud Storage
- Azure Blob Storage

---

## Migration from Railway

If you need full HIPAA compliance and Railway Enterprise is too expensive:

### Migrate to AWS:
1. Export database
2. Upload files to S3
3. Deploy on EC2 or ECS
4. Configure RDS for database

### Migrate to Azure:
1. Export data
2. Deploy to Azure App Service
3. Use Azure Database for PostgreSQL
4. Configure Azure Blob Storage

See `HIPAA_COMPLIANCE.md` for detailed migration guides.

---

## Troubleshooting

### Deployment Fails:
- Check build logs
- Verify requirements.txt is correct
- Ensure environment variables are set

### Database Errors:
- Check if volume is mounted correctly
- Verify DB_ENCRYPTION_KEY is set
- Check file permissions

### Out of Memory:
- Increase service resources in Railway
- Optimize file processing
- Use streaming for large files

### Slow Performance:
- Upgrade Railway plan
- Add more workers in Procfile
- Optimize database queries

---

## Support

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Enterprise Sales: enterprise@railway.app

---

**Remember: Standard Railway plans are NOT HIPAA compliant. Use only for development/testing with synthetic data!**

