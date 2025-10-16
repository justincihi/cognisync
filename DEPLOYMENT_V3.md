# WellTech AI MedSuite™ v3.0.0 - Deployment Guide

## 🎉 What's New in v3.0.0

### Major Features
- **Complete User Management System** with authentication and authorization
- **Role-Based Access Control** (Admin & Clinician roles)
- **Professional Registration** with license validation
- **Admin Dashboard** for user management and system oversight
- **JWT Token Authentication** for secure API access
- **Rebranded** from ThinkSync™ to WellTech AI MedSuite™

### Security Enhancements
- Password hashing with salt
- Account lockout after failed login attempts
- Admin approval workflow for new users
- Session isolation per user
- Comprehensive audit logging

## 📋 Prerequisites

- Python 3.11+
- pip3
- Git

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/justincihi/thinksync-enhanced.git
cd thinksync-enhanced
```

### 2. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Run the Application

```bash
python3 app.py
```

The application will start on **http://localhost:8080**

## 🔐 Admin Access

**Default Admin Credentials:**
- Username: `admin`
- Password: `3942-granite-35`

⚠️ **Important:** Change the admin password after first login in production environments.

## 📊 Database Schema

The application uses SQLite with the following tables:

### Users Table
- User authentication and profile information
- License verification data
- Role and status management
- Login attempt tracking

### Therapy Sessions Table
- Session data linked to specific users
- Analysis results and sentiment data
- Transcript and validation information

### User Sessions Table
- Active session tokens
- Session expiration tracking
- IP and user agent logging

### Audit Log Table
- Security event tracking
- User action logging
- System activity monitoring

### User Preferences Table
- User-specific settings
- Theme and notification preferences
- Default therapy type and output format

## 🔑 API Authentication

All protected endpoints require JWT token authentication:

```bash
# Login to get token
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin", "password": "3942-granite-35"}'

# Use token in subsequent requests
curl http://localhost:8080/api/auth/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📝 API Endpoints

### Public Endpoints
- `GET /` - Main application interface
- `GET /mobile` - Mobile upload interface
- `GET /api/health` - Health check endpoint
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/therapy/demo` - Demo analysis (no auth required)

### Protected Endpoints (Require Authentication)
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile
- `POST /api/therapy/sessions` - Create therapy session
- `GET /api/therapy/sessions` - List user's sessions

### Admin Endpoints (Require Admin Role)
- `GET /api/admin/users` - List all users
- `POST /api/admin/users/<id>/approve` - Approve user
- `POST /api/admin/users/<id>/reject` - Reject user
- `GET /api/admin/stats` - Get system statistics

## 👥 User Registration Flow

1. **User submits registration** with:
   - Email
   - Password (minimum 8 characters)
   - Full name
   - License type
   - License number
   - State of licensure

2. **Account created** with status: `pending`

3. **Admin reviews** and approves/rejects the account

4. **User can login** once status is `active`

## 🛡️ Security Features

### Password Security
- SHA-256 hashing with unique salt per user
- Minimum 8 character requirement
- Salt stored with hash for verification

### Account Protection
- Failed login attempt tracking
- Automatic account lockout (30 minutes) after 5 failed attempts
- Admin can unlock accounts manually

### Session Management
- JWT tokens expire after 24 hours
- Tokens include user ID, email, and role
- All API requests validated against token

### Audit Logging
- All user actions logged with:
  - User ID
  - Action type
  - Timestamp
  - IP address
  - User agent

## 🔧 Configuration

### Environment Variables

```bash
# Application secret key
export SECRET_KEY="your-secret-key-here"

# JWT secret key (auto-generated if not set)
export JWT_SECRET_KEY="your-jwt-secret-here"

# Optional: Set custom port
export PORT=8080
```

### Database Location

Default: `welltech_medsuite.db` in the application directory

To use a different location, modify the `get_db()` function in `app.py`.

## 📱 Mobile Interface

Access the mobile-optimized upload interface at:
```
http://localhost:8080/mobile
```

Features:
- Touch-friendly file upload
- Simplified form fields
- Responsive design for all devices

## 🔄 Upgrading from v2.x

1. **Backup your database:**
   ```bash
   cp thinksync_fresh.db thinksync_fresh.db.backup
   ```

2. **Pull latest changes:**
   ```bash
   git pull origin main
   git checkout v3.0.0
   ```

3. **Install new dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Restart the application:**
   ```bash
   python3 app.py
   ```

The database will automatically migrate to the new schema on first run.

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>
```

### Database Locked
```bash
# Ensure no other instances are running
ps aux | grep "python3 app.py"

# Kill any running instances
pkill -f "python3 app.py"
```

### JWT Token Errors
- Ensure `PyJWT` is installed: `pip3 install PyJWT`
- Check token hasn't expired (24-hour lifetime)
- Verify Authorization header format: `Bearer <token>`

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8080/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "WellTech AI MedSuite™",
  "version": "3.0.0",
  "platform": "Integrated Edition - Port 8080",
  "timestamp": "2025-10-06T...",
  "features": [...]
}
```

### Admin Statistics
Login as admin and access:
```bash
curl http://localhost:8080/api/admin/stats \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## 🔮 Future Enhancements

- Email verification system
- Password reset functionality
- Two-factor authentication
- Advanced user permissions
- Session export in multiple formats
- Real-time collaboration features
- Integration with EHR systems

## 📞 Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/justincihi/thinksync-enhanced/issues
- Email: justin@cadenzatherapeutics.com

## 📄 License

Proprietary - All Rights Reserved  
© 2024 All Rights Reserved

---

**WellTech AI MedSuite™** - Professional Clinical AI Solutions  
*Formerly ThinkSync™ Enhanced Edition*
