# Cognisync™

**AI-Powered Clinical Documentation System with Advanced Sentiment Analysis**

Cognisync™ is a comprehensive clinical documentation platform that leverages artificial intelligence to transform therapy session recordings into professional clinical notes with advanced sentiment analysis and file management capabilities.

## 🌟 Features

### Core Capabilities
- **AI-Powered Analysis**: Automated SOAP/BIRP note generation from audio recordings
- **Advanced Sentiment Analysis**: Real-time emotional state tracking and analysis
- **Multi-Format Support**: MP3, WAV, M4A, MP4, WebM, OGG audio files
- **Mobile-Optimized Interface**: Responsive design for on-the-go documentation

### User Management
- **Secure Authentication**: JWT token-based authentication system
- **Role-Based Access Control**: Admin and Clinician roles with appropriate permissions
- **Professional Registration**: License verification and admin approval workflow
- **Admin Dashboard**: Comprehensive user and system management

### File Management (v3.1.0)
- **Automatic File Storage**: All uploaded files are saved to disk
- **File Download**: Retrieve previously uploaded audio files
- **File Listing**: View all your uploaded files with metadata
- **File Deletion**: Remove unwanted files securely
- **User Isolation**: Files are isolated by user for privacy

### Clinical Documentation
- **SOAP Notes**: Subjective, Objective, Assessment, Plan format
- **BIRP Notes**: Behavior, Intervention, Response, Plan format
- **Custom Formats**: Flexible documentation options
- **Export Capabilities**: Multiple export formats supported

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip3
- Virtual environment (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/justincihi/cognisync.git
cd cognisync

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Run the application
python3 app.py
```

The application will be available at `http://localhost:8080`

### Default Admin Credentials
- **Username**: `admin`
- **Password**: `3942-granite-35`

## 📁 File Management API

### List Files
```bash
GET /api/files/list
Authorization: Bearer {token}
```

### Download File
```bash
GET /api/files/{session_id}/download
Authorization: Bearer {token}
```

### Delete File
```bash
DELETE /api/files/{session_id}
Authorization: Bearer {token}
```

## 🏗️ Architecture

```
cognisync/
├── app.py                      # Main application file
├── file_management.py          # File management module
├── user_management.py          # User authentication module
├── auth_routes.py              # Authentication routes
├── admin_dashboard.py          # Admin functionality
├── src/
│   ├── main.py                 # Deployment entry point
│   ├── file_management.py      # File management (deployment)
│   └── static/                 # Frontend assets
├── static/                     # Static files
│   ├── index.html              # Main interface
│   ├── mobile-upload.html      # Mobile interface
│   └── assets/                 # CSS, JS, images
├── uploads/                    # Uploaded audio files
└── requirements.txt            # Python dependencies
```

## 🔐 Security

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Salted password storage
- **Account Lockout**: Protection against brute force attacks
- **Audit Logging**: Comprehensive activity tracking
- **File Isolation**: User-specific file access control
- **HIPAA Considerations**: Designed with healthcare compliance in mind

## 📊 Database Schema

SQLite database with the following key tables:
- `users`: User accounts and authentication
- `therapy_sessions`: Session data and analysis results
- `audit_log`: System activity tracking

## 🌐 Deployment

The application can be deployed to various platforms:
- Local development server
- Cloud platforms (AWS, Google Cloud, Azure)
- Container platforms (Docker, Kubernetes)
- Serverless platforms

See `DEPLOYMENT_V3.md` for detailed deployment instructions.

## 📚 Documentation

- `FILE_MANAGEMENT_GUIDE.md` - Complete file management API documentation
- `DEPLOYMENT_V3.md` - Deployment guide
- `RELEASE_NOTES_V3.md` - Version history and changes

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: React with modern UI components
- **Database**: SQLite
- **Authentication**: JWT tokens
- **AI Integration**: OpenAI API, Gemini API

## 📝 License

Proprietary - All Rights Reserved

This application was developed by Justin Cihi as part of the proprietary AI clinical documentation suite.

## ⚠️ Regulatory Notice

This application is designed as an informational aid for healthcare professionals. It does not replace professional clinical judgment but serves to enhance and inform the diagnostic and mental health treatment that human clinicians provide to their clients.

## 🤝 Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/justincihi/cognisync/issues
- Email: [Your contact email]

## 📈 Version History

- **v3.1.0** (Current) - File Management System
  - Automatic file storage
  - File download/delete APIs
  - User file isolation
  - Comprehensive documentation

- **v3.0.0** - User Management & Authentication
  - Complete authentication system
  - Role-based access control
  - Admin dashboard
  - License verification

- **v2.0.0** - Sentiment Analysis Integration
  - Advanced emotional analysis
  - Real-time sentiment tracking
  - Enhanced SOAP/BIRP notes

- **v1.0.0** - Initial Release
  - Basic audio upload
  - AI-powered note generation
  - SOAP/BIRP formats

---

**Made with ❤️ for Healthcare Professionals**

Cognisync™ - Transforming Clinical Documentation
