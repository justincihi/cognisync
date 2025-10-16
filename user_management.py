#!/usr/bin/env python3
"""
ThinkSync™ User Management System
Developed for WellTech AI MedSuite™
Complete Authentication & Role-Based Access Control
"""

import os
import sqlite3
import hashlib
import secrets
import jwt
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from flask import request, jsonify, session
from functools import wraps

class UserManager:
    def __init__(self, db_path='user_management.db'):
        self.db_path = db_path
        self.secret_key = os.environ.get('JWT_SECRET_KEY', secrets.token_hex(32))
        self.init_database()
        self.create_admin_user()
    
    def init_database(self):
        """Initialize the user management database with comprehensive schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table with comprehensive fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                license_type TEXT,
                license_number TEXT,
                state_of_licensure TEXT,
                role TEXT DEFAULT 'clinician',
                status TEXT DEFAULT 'pending',
                email_verified BOOLEAN DEFAULT FALSE,
                verification_token TEXT,
                reset_token TEXT,
                reset_token_expires DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                login_attempts INTEGER DEFAULT 0,
                locked_until DATETIME
            )
        ''')
        
        # User sessions table for session management
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Audit log table for security tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                theme TEXT DEFAULT 'dark',
                notifications BOOLEAN DEFAULT TRUE,
                auto_save BOOLEAN DEFAULT TRUE,
                default_therapy_type TEXT DEFAULT 'CBT',
                default_output_format TEXT DEFAULT 'SOAP',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_admin_user(self):
        """Create default admin user if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute('SELECT id FROM users WHERE email = ?', ('admin@thinksync.com',))
        if not cursor.fetchone():
            # Create admin user
            password_hash = self.hash_password('3942-granite-35')
            cursor.execute('''
                INSERT INTO users (email, password_hash, full_name, role, status, email_verified)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('admin@thinksync.com', password_hash, 'System Administrator', 'admin', 'active', True))
            
            admin_id = cursor.lastrowid
            
            # Create admin preferences
            cursor.execute('''
                INSERT INTO user_preferences (user_id) VALUES (?)
            ''', (admin_id,))
            
            # Log admin creation
            cursor.execute('''
                INSERT INTO audit_log (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (admin_id, 'admin_created', 'System administrator account created'))
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password, stored_hash):
        """Verify password against stored hash"""
        try:
            salt, hash_value = stored_hash.split(':')
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return password_hash == hash_value
        except ValueError:
            return False
    
    def generate_jwt_token(self, user_id, email, role):
        """Generate JWT token for user authentication"""
        payload = {
            'user_id': user_id,
            'email': email,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_jwt_token(self, token):
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def register_user(self, user_data):
        """Register a new user with validation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Validate required fields
            required_fields = ['email', 'password', 'full_name', 'license_type', 'license_number', 'state_of_licensure']
            for field in required_fields:
                if not user_data.get(field):
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # Check if user already exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (user_data['email'],))
            if cursor.fetchone():
                return {'success': False, 'error': 'User with this email already exists'}
            
            # Generate verification token
            verification_token = secrets.token_urlsafe(32)
            
            # Hash password
            password_hash = self.hash_password(user_data['password'])
            
            # Insert user
            cursor.execute('''
                INSERT INTO users (email, password_hash, full_name, license_type, 
                                 license_number, state_of_licensure, verification_token)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_data['email'],
                password_hash,
                user_data['full_name'],
                user_data['license_type'],
                user_data['license_number'],
                user_data['state_of_licensure'],
                verification_token
            ))
            
            user_id = cursor.lastrowid
            
            # Create user preferences
            cursor.execute('INSERT INTO user_preferences (user_id) VALUES (?)', (user_id,))
            
            # Log registration
            cursor.execute('''
                INSERT INTO audit_log (user_id, action, details, ip_address)
                VALUES (?, ?, ?, ?)
            ''', (user_id, 'user_registered', f'New user registered: {user_data["email"]}', 
                  request.remote_addr if request else None))
            
            conn.commit()
            
            # Send verification email (in production)
            # self.send_verification_email(user_data['email'], verification_token)
            
            return {
                'success': True,
                'message': 'User registered successfully. Please wait for admin approval.',
                'user_id': user_id,
                'verification_token': verification_token
            }
            
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def authenticate_user(self, email, password):
        """Authenticate user login"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get user data
            cursor.execute('''
                SELECT id, email, password_hash, full_name, role, status, 
                       login_attempts, locked_until
                FROM users WHERE email = ?
            ''', (email,))
            
            user = cursor.fetchone()
            if not user:
                return {'success': False, 'error': 'Invalid email or password'}
            
            user_id, email, password_hash, full_name, role, status, login_attempts, locked_until = user
            
            # Check if account is locked
            if locked_until and datetime.fromisoformat(locked_until) > datetime.now():
                return {'success': False, 'error': 'Account temporarily locked due to multiple failed attempts'}
            
            # Check account status
            if status != 'active':
                return {'success': False, 'error': f'Account status: {status}. Please contact administrator.'}
            
            # Verify password
            if not self.verify_password(password, password_hash):
                # Increment login attempts
                new_attempts = login_attempts + 1
                locked_until = None
                if new_attempts >= 5:
                    locked_until = (datetime.now() + timedelta(minutes=30)).isoformat()
                
                cursor.execute('''
                    UPDATE users SET login_attempts = ?, locked_until = ?
                    WHERE id = ?
                ''', (new_attempts, locked_until, user_id))
                
                # Log failed attempt
                cursor.execute('''
                    INSERT INTO audit_log (user_id, action, details, ip_address)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, 'login_failed', f'Failed login attempt #{new_attempts}', 
                      request.remote_addr if request else None))
                
                conn.commit()
                return {'success': False, 'error': 'Invalid email or password'}
            
            # Successful login - reset attempts and update last login
            cursor.execute('''
                UPDATE users SET login_attempts = 0, locked_until = NULL, 
                               last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id,))
            
            # Generate JWT token
            token = self.generate_jwt_token(user_id, email, role)
            
            # Create session record
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            cursor.execute('''
                INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, session_token, expires_at, 
                  request.remote_addr if request else None,
                  request.headers.get('User-Agent') if request else None))
            
            # Log successful login
            cursor.execute('''
                INSERT INTO audit_log (user_id, action, details, ip_address)
                VALUES (?, ?, ?, ?)
            ''', (user_id, 'login_success', 'User logged in successfully', 
                  request.remote_addr if request else None))
            
            conn.commit()
            
            return {
                'success': True,
                'token': token,
                'user': {
                    'id': user_id,
                    'email': email,
                    'full_name': full_name,
                    'role': role
                },
                'session_token': session_token
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id):
        """Get user data by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, full_name, license_type, license_number, 
                   state_of_licensure, role, status, email_verified, 
                   created_at, last_login
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'email': user[1],
                'full_name': user[2],
                'license_type': user[3],
                'license_number': user[4],
                'state_of_licensure': user[5],
                'role': user[6],
                'status': user[7],
                'email_verified': user[8],
                'created_at': user[9],
                'last_login': user[10]
            }
        return None
    
    def get_all_users(self, admin_user_id):
        """Get all users (admin only)"""
        # Verify admin role
        admin_user = self.get_user_by_id(admin_user_id)
        if not admin_user or admin_user['role'] != 'admin':
            return {'success': False, 'error': 'Unauthorized access'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, full_name, license_type, license_number, 
                   state_of_licensure, role, status, email_verified, 
                   created_at, last_login
            FROM users ORDER BY created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'email': row[1],
                'full_name': row[2],
                'license_type': row[3],
                'license_number': row[4],
                'state_of_licensure': row[5],
                'role': row[6],
                'status': row[7],
                'email_verified': row[8],
                'created_at': row[9],
                'last_login': row[10]
            })
        
        conn.close()
        return {'success': True, 'users': users}
    
    def update_user_status(self, admin_user_id, user_id, new_status):
        """Update user status (admin only)"""
        # Verify admin role
        admin_user = self.get_user_by_id(admin_user_id)
        if not admin_user or admin_user['role'] != 'admin':
            return {'success': False, 'error': 'Unauthorized access'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET status = ? WHERE id = ?', (new_status, user_id))
        
        # Log status change
        cursor.execute('''
            INSERT INTO audit_log (user_id, action, details)
            VALUES (?, ?, ?)
        ''', (admin_user_id, 'status_changed', f'Changed user {user_id} status to {new_status}'))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': f'User status updated to {new_status}'}
    
    def get_user_sessions(self, user_id):
        """Get user's therapy sessions"""
        conn = sqlite3.connect('thinksync_fresh.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, client_name, therapy_type, summary_format, 
                   created_at, confidence_score
            FROM therapy_sessions 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'id': row[0],
                'client_name': row[1],
                'therapy_type': row[2],
                'summary_format': row[3],
                'created_at': row[4],
                'confidence_score': row[5]
            })
        
        conn.close()
        return sessions
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM user_sessions WHERE expires_at < ?', (datetime.now(),))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return deleted_count

# Authentication decorators
def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No authorization token provided'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        user_manager = UserManager()
        payload = user_manager.verify_jwt_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user info to request context
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user') or request.current_user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated_function

def require_active_user(f):
    """Decorator to require active user status"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user'):
            return jsonify({'error': 'Authentication required'}), 401
        
        user_manager = UserManager()
        user = user_manager.get_user_by_id(request.current_user['user_id'])
        
        if not user or user['status'] != 'active':
            return jsonify({'error': 'Account not active'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

