#!/usr/bin/env python3
"""
ThinkSync™ Authentication Routes
Developed for WellTech AI MedSuite™
Complete Authentication & User Management API
"""

from flask import Blueprint, request, jsonify, render_template_string
from user_management import UserManager, require_auth, require_admin, require_active_user
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
user_manager = UserManager()

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data.get('email', '')):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Validate password strength
        password = data.get('password', '')
        if len(password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters long'}), 400
        
        # Validate license number format (basic validation)
        license_number = data.get('license_number', '')
        if not license_number or len(license_number) < 3:
            return jsonify({'success': False, 'error': 'Valid license number is required'}), 400
        
        result = user_manager.register_user(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        result = user_manager.authenticate_user(email, password)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """User logout endpoint"""
    try:
        # In a full implementation, we would invalidate the session token
        return jsonify({'success': True, 'message': 'Logged out successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@require_auth
@require_active_user
def get_profile():
    """Get user profile"""
    try:
        user = user_manager.get_user_by_id(request.current_user['user_id'])
        if user:
            # Remove sensitive data
            user.pop('password_hash', None)
            return jsonify({'success': True, 'user': user}), 200
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/sessions', methods=['GET'])
@require_auth
@require_active_user
def get_user_sessions():
    """Get user's therapy sessions"""
    try:
        sessions = user_manager.get_user_sessions(request.current_user['user_id'])
        return jsonify({'success': True, 'sessions': sessions}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Admin routes
@auth_bp.route('/admin/users', methods=['GET'])
@require_auth
@require_admin
def get_all_users():
    """Get all users (admin only)"""
    try:
        result = user_manager.get_all_users(request.current_user['user_id'])
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/admin/users/<int:user_id>/status', methods=['PUT'])
@require_auth
@require_admin
def update_user_status(user_id):
    """Update user status (admin only)"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pending', 'active', 'suspended', 'inactive']:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        
        result = user_manager.update_user_status(
            request.current_user['user_id'], user_id, new_status
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/admin/stats', methods=['GET'])
@require_auth
@require_admin
def get_admin_stats():
    """Get admin dashboard statistics"""
    try:
        import sqlite3
        
        conn = sqlite3.connect('user_management.db')
        cursor = conn.cursor()
        
        # Get user statistics
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "active"')
        active_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "pending"')
        pending_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE created_at >= date("now", "-7 days")')
        new_users_week = cursor.fetchone()[0]
        
        # Get session statistics
        try:
            cursor.execute('SELECT COUNT(*) FROM therapy_sessions')
            total_sessions = cursor.fetchone()[0] or 0
        except:
            total_sessions = 0
        
        try:
            cursor.execute('SELECT COUNT(*) FROM therapy_sessions WHERE created_at >= date("now", "-7 days")')
            sessions_week = cursor.fetchone()[0] or 0
        except:
            sessions_week = 0
        
        conn.close()
        
        stats = {
            'users': {
                'total': total_users,
                'active': active_users,
                'pending': pending_users,
                'new_this_week': new_users_week
            },
            'sessions': {
                'total': total_sessions,
                'this_week': sessions_week
            }
        }
        
        return jsonify({'success': True, 'stats': stats}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Registration form route
@auth_bp.route('/register-form', methods=['GET'])
def registration_form():
    """Serve registration form"""
    form_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ThinkSync™ Clinician Registration - WellTech AI MedSuite™</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #ffffff;
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 20px;
                padding: 40px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            .logo {
                font-size: 2.5em;
                font-weight: bold;
                background: linear-gradient(45deg, #00d4ff, #0099cc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 10px;
            }
            
            .subtitle {
                color: #a0a0a0;
                font-size: 1.1em;
            }
            
            .form-group {
                margin-bottom: 25px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #00d4ff;
            }
            
            input, select {
                width: 100%;
                padding: 15px;
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.05);
                color: #ffffff;
                font-size: 16px;
                transition: all 0.3s ease;
            }
            
            input:focus, select:focus {
                outline: none;
                border-color: #00d4ff;
                box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
            }
            
            .submit-btn {
                width: 100%;
                padding: 18px;
                background: linear-gradient(45deg, #00d4ff, #0099cc);
                border: none;
                border-radius: 10px;
                color: white;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-top: 20px;
            }
            
            .submit-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 30px rgba(0, 212, 255, 0.4);
            }
            
            .message {
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .success {
                background: rgba(0, 255, 0, 0.1);
                border: 1px solid rgba(0, 255, 0, 0.3);
                color: #00ff00;
            }
            
            .error {
                background: rgba(255, 0, 0, 0.1);
                border: 1px solid rgba(255, 0, 0, 0.3);
                color: #ff6b6b;
            }
            
            .login-link {
                text-align: center;
                margin-top: 30px;
                padding-top: 30px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .login-link a {
                color: #00d4ff;
                text-decoration: none;
                font-weight: 600;
            }
            
            .login-link a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">ThinkSync™</div>
                <div class="subtitle">Clinician Registration - WellTech AI MedSuite™</div>
            </div>
            
            <div id="message"></div>
            
            <form id="registrationForm">
                <div class="form-group">
                    <label for="full_name">Full Name *</label>
                    <input type="text" id="full_name" name="full_name" required>
                </div>
                
                <div class="form-group">
                    <label for="email">Email Address (Username) *</label>
                    <input type="email" id="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password *</label>
                    <input type="password" id="password" name="password" required minlength="8">
                </div>
                
                <div class="form-group">
                    <label for="password_confirm">Confirm Password *</label>
                    <input type="password" id="password_confirm" name="password_confirm" required>
                </div>
                
                <div class="form-group">
                    <label for="license_type">License Type *</label>
                    <select id="license_type" name="license_type" required>
                        <option value="">Select License Type</option>
                        <option value="LCSW">Licensed Clinical Social Worker (LCSW)</option>
                        <option value="LPC">Licensed Professional Counselor (LPC)</option>
                        <option value="LMFT">Licensed Marriage & Family Therapist (LMFT)</option>
                        <option value="LMHC">Licensed Mental Health Counselor (LMHC)</option>
                        <option value="PhD">Doctor of Philosophy (PhD) in Psychology</option>
                        <option value="PsyD">Doctor of Psychology (PsyD)</option>
                        <option value="MD">Medical Doctor (MD) - Psychiatrist</option>
                        <option value="Other">Other (Please specify in license number field)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="license_number">License Number *</label>
                    <input type="text" id="license_number" name="license_number" required>
                </div>
                
                <div class="form-group">
                    <label for="state_of_licensure">State of Licensure *</label>
                    <select id="state_of_licensure" name="state_of_licensure" required>
                        <option value="">Select State</option>
                        <option value="AL">Alabama</option>
                        <option value="AK">Alaska</option>
                        <option value="AZ">Arizona</option>
                        <option value="AR">Arkansas</option>
                        <option value="CA">California</option>
                        <option value="CO">Colorado</option>
                        <option value="CT">Connecticut</option>
                        <option value="DE">Delaware</option>
                        <option value="FL">Florida</option>
                        <option value="GA">Georgia</option>
                        <option value="HI">Hawaii</option>
                        <option value="ID">Idaho</option>
                        <option value="IL">Illinois</option>
                        <option value="IN">Indiana</option>
                        <option value="IA">Iowa</option>
                        <option value="KS">Kansas</option>
                        <option value="KY">Kentucky</option>
                        <option value="LA">Louisiana</option>
                        <option value="ME">Maine</option>
                        <option value="MD">Maryland</option>
                        <option value="MA">Massachusetts</option>
                        <option value="MI">Michigan</option>
                        <option value="MN">Minnesota</option>
                        <option value="MS">Mississippi</option>
                        <option value="MO">Missouri</option>
                        <option value="MT">Montana</option>
                        <option value="NE">Nebraska</option>
                        <option value="NV">Nevada</option>
                        <option value="NH">New Hampshire</option>
                        <option value="NJ">New Jersey</option>
                        <option value="NM">New Mexico</option>
                        <option value="NY">New York</option>
                        <option value="NC">North Carolina</option>
                        <option value="ND">North Dakota</option>
                        <option value="OH">Ohio</option>
                        <option value="OK">Oklahoma</option>
                        <option value="OR">Oregon</option>
                        <option value="PA">Pennsylvania</option>
                        <option value="RI">Rhode Island</option>
                        <option value="SC">South Carolina</option>
                        <option value="SD">South Dakota</option>
                        <option value="TN">Tennessee</option>
                        <option value="TX">Texas</option>
                        <option value="UT">Utah</option>
                        <option value="VT">Vermont</option>
                        <option value="VA">Virginia</option>
                        <option value="WA">Washington</option>
                        <option value="WV">West Virginia</option>
                        <option value="WI">Wisconsin</option>
                        <option value="WY">Wyoming</option>
                    </select>
                </div>
                
                <button type="submit" class="submit-btn">Register for ThinkSync™</button>
            </form>
            
            <div class="login-link">
                Already have an account? <a href="/login">Login here</a>
            </div>
        </div>
        
        <script>
            document.getElementById('registrationForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const data = Object.fromEntries(formData);
                
                // Validate passwords match
                if (data.password !== data.password_confirm) {
                    showMessage('Passwords do not match', 'error');
                    return;
                }
                
                // Remove password confirmation from data
                delete data.password_confirm;
                
                try {
                    const response = await fetch('/api/auth/register', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        showMessage('Registration successful! Please wait for admin approval before logging in.', 'success');
                        this.reset();
                    } else {
                        showMessage(result.error, 'error');
                    }
                } catch (error) {
                    showMessage('Registration failed. Please try again.', 'error');
                }
            });
            
            function showMessage(text, type) {
                const messageDiv = document.getElementById('message');
                messageDiv.innerHTML = `<div class="message ${type}">${text}</div>`;
                setTimeout(() => {
                    messageDiv.innerHTML = '';
                }, 5000);
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(form_html)

# Login form route
@auth_bp.route('/login-form', methods=['GET'])
def login_form():
    """Serve login form"""
    form_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ThinkSync™ Login - WellTech AI MedSuite™</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #ffffff;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .container {
                max-width: 400px;
                width: 100%;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 20px;
                padding: 40px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            .logo {
                font-size: 2.5em;
                font-weight: bold;
                background: linear-gradient(45deg, #00d4ff, #0099cc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 10px;
            }
            
            .subtitle {
                color: #a0a0a0;
                font-size: 1.1em;
            }
            
            .form-group {
                margin-bottom: 25px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #00d4ff;
            }
            
            input {
                width: 100%;
                padding: 15px;
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.05);
                color: #ffffff;
                font-size: 16px;
                transition: all 0.3s ease;
            }
            
            input:focus {
                outline: none;
                border-color: #00d4ff;
                box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
            }
            
            .submit-btn {
                width: 100%;
                padding: 18px;
                background: linear-gradient(45deg, #00d4ff, #0099cc);
                border: none;
                border-radius: 10px;
                color: white;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-top: 20px;
            }
            
            .submit-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 30px rgba(0, 212, 255, 0.4);
            }
            
            .message {
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .success {
                background: rgba(0, 255, 0, 0.1);
                border: 1px solid rgba(0, 255, 0, 0.3);
                color: #00ff00;
            }
            
            .error {
                background: rgba(255, 0, 0, 0.1);
                border: 1px solid rgba(255, 0, 0, 0.3);
                color: #ff6b6b;
            }
            
            .register-link {
                text-align: center;
                margin-top: 30px;
                padding-top: 30px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .register-link a {
                color: #00d4ff;
                text-decoration: none;
                font-weight: 600;
            }
            
            .register-link a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">ThinkSync™</div>
                <div class="subtitle">WellTech AI MedSuite™</div>
            </div>
            
            <div id="message"></div>
            
            <form id="loginForm">
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <button type="submit" class="submit-btn">Login to ThinkSync™</button>
            </form>
            
            <div class="register-link">
                Don't have an account? <a href="/api/auth/register-form">Register here</a>
            </div>
        </div>
        
        <script>
            document.getElementById('loginForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const data = Object.fromEntries(formData);
                
                try {
                    const response = await fetch('/api/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        // Store token in localStorage
                        localStorage.setItem('thinksync_token', result.token);
                        localStorage.setItem('thinksync_user', JSON.stringify(result.user));
                        
                        showMessage('Login successful! Redirecting...', 'success');
                        
                        // Redirect based on user role
                        setTimeout(() => {
                            if (result.user.role === 'admin') {
                                window.location.href = '/admin';
                            } else {
                                window.location.href = '/';
                            }
                        }, 1500);
                    } else {
                        showMessage(result.error, 'error');
                    }
                } catch (error) {
                    showMessage('Login failed. Please try again.', 'error');
                }
            });
            
            function showMessage(text, type) {
                const messageDiv = document.getElementById('message');
                messageDiv.innerHTML = `<div class="message ${type}">${text}</div>`;
                if (type !== 'success') {
                    setTimeout(() => {
                        messageDiv.innerHTML = '';
                    }, 5000);
                }
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(form_html)

