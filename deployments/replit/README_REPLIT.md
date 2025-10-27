# CogniSync™ - Replit Deployment Guide

## ⚠️ IMPORTANT HIPAA WARNING

**Replit is NOT HIPAA compliant and should ONLY be used for:**
- Development and testing
- Demonstrations
- Training with synthetic data

**DO NOT use Replit for:**
- Real patient data
- Production clinical environments
- Any PHI (Protected Health Information)

---

## Quick Start on Replit

### 1. Create New Repl

1. Go to [Replit](https://replit.com)
2. Click "Create Repl"
3. Select "Import from GitHub"
4. Enter: `https://github.com/justincihi/cognisync`
5. Click "Import from GitHub"

### 2. Configure Environment Variables

Click on "Secrets" (lock icon) and add:

```
# Required
DB_ENCRYPTION_KEY=<generate_using_python>
FILE_ENCRYPTION_KEY=<generate_using_python>
OPENAI_API_KEY=<your_openai_key>
ANTHROPIC_API_KEY=<your_anthropic_key>

# Optional
USE_REAL_AI=true
SESSION_TIMEOUT_MINUTES=15
DATA_RETENTION_YEARS=7
```

### 3. Generate Encryption Keys

In the Replit Shell, run:

```bash
python3 << 'EOF'
from cryptography.fernet import Fernet
print("DB_ENCRYPTION_KEY=" + Fernet.generate_key().decode())
print("FILE_ENCRYPTION_KEY=" + Fernet.generate_key().decode())
EOF
```

Copy these keys to your Secrets.

### 4. Install Dependencies

```bash
pip install -r requirements_hipaa.txt
```

### 5. Run the Application

Click the "Run" button or:

```bash
python3 app.py
```

### 6. Access the Application

The application will be available at your Repl URL (e.g., `https://your-repl-name.your-username.repl.co`)

---

## File Structure for Replit

```
cognisync/
├── app.py                 # Main application
├── encrypted_db.py        # Database encryption
├── file_encryption.py     # File encryption
├── audit_logger.py        # Audit logging
├── mfa_auth.py           # Multi-factor auth
├── data_retention.py     # Data retention
├── ai_service.py         # AI integration
├── requirements_hipaa.txt # Dependencies
├── static/               # Frontend files
│   ├── index.html
│   └── cognisync-logo.png
└── uploads/              # Encrypted file storage
```

---

## Limitations on Replit

### ❌ Not HIPAA Compliant Because:

1. **No BAA**: Replit doesn't sign Business Associate Agreements
2. **Shared Infrastructure**: Multi-tenant environment
3. **No Encryption at Rest**: Replit storage is not encrypted
4. **Limited Audit Logging**: Insufficient for HIPAA requirements
5. **No Physical Safeguards**: Cannot verify data center security

### ⚠️ Technical Limitations:

1. **Storage**: Limited disk space (may need to delete old sessions)
2. **Memory**: Limited RAM (large files may fail)
3. **Uptime**: Repls sleep after inactivity
4. **Performance**: Shared resources, slower than dedicated hosting

---

## Recommended Use Cases

### ✅ Good For:

- **Development**: Testing new features
- **Demos**: Showing functionality to stakeholders
- **Training**: Using synthetic patient data
- **Prototyping**: Rapid iteration

### ❌ Not Good For:

- **Production**: Real clinical use
- **PHI**: Any real patient information
- **Compliance**: HIPAA-regulated environments
- **Scale**: High-volume usage

---

## Migration to Production

When ready for real patient data, migrate to:

1. **AWS**: Most comprehensive HIPAA support
2. **Azure**: Best for Azure OpenAI integration
3. **Google Cloud**: Good balance of features and cost

See `HIPAA_COMPLIANCE.md` for detailed migration guide.

---

## Troubleshooting

### Repl Keeps Sleeping

- Upgrade to Replit Hacker plan ($7/month)
- Or use a service like UptimeRobot to ping your Repl

### Out of Memory

- Reduce file size limits
- Delete old sessions regularly
- Upgrade to higher tier

### Slow Performance

- This is normal on free tier
- Consider upgrading or migrating to dedicated hosting

---

## Support

For issues specific to Replit deployment:
1. Check Replit documentation
2. Review application logs in the Console
3. Check environment variables are set correctly

For application issues:
- See main README.md
- Check GitHub issues

---

**Remember: Replit is for DEVELOPMENT ONLY. Never use with real patient data!**

