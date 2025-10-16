#!/usr/bin/env python3
"""
ThinkSync™ Admin Dashboard
Developed for WellTech AI MedSuite™
Complete Administrative Interface
"""

from flask import Blueprint, render_template_string, request, jsonify
from user_management import UserManager, require_auth, require_admin

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
user_manager = UserManager()

@admin_bp.route('/')
@require_auth
@require_admin
def admin_dashboard():
    """Serve admin dashboard"""
    dashboard_html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ThinkSync™ Admin Dashboard - WellTech AI MedSuite™</title>
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
            }
            
            .header {
                background: rgba(255, 255, 255, 0.05);
                padding: 20px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
            }
            
            .header-content {
                max-width: 1200px;
                margin: 0 auto;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .logo {
                font-size: 1.8em;
                font-weight: bold;
                background: linear-gradient(45deg, #00d4ff, #0099cc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .user-info {
                display: flex;
                align-items: center;
                gap: 20px;
            }
            
            .logout-btn {
                padding: 10px 20px;
                background: linear-gradient(45deg, #ff4757, #ff3742);
                border: none;
                border-radius: 8px;
                color: white;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            
            .logout-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(255, 71, 87, 0.4);
            }
            
            .main-content {
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
            }
            
            .dashboard-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
                margin-bottom: 40px;
            }
            
            .card {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 20px;
                padding: 30px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                transition: all 0.3s ease;
            }
            
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            }
            
            .card-title {
                font-size: 1.3em;
                font-weight: bold;
                margin-bottom: 20px;
                color: #00d4ff;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .stat-number {
                font-size: 2.5em;
                font-weight: bold;
                color: #00ff88;
                margin-bottom: 10px;
            }
            
            .stat-label {
                color: #a0a0a0;
                font-size: 0.9em;
            }
            
            .users-table {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 20px;
                padding: 30px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                overflow-x: auto;
            }
            
            .table-header {
                font-size: 1.3em;
                font-weight: bold;
                margin-bottom: 20px;
                color: #00d4ff;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            
            th, td {
                padding: 15px;
                text-align: left;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            th {
                background: rgba(0, 212, 255, 0.1);
                color: #00d4ff;
                font-weight: 600;
            }
            
            .status-badge {
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 0.8em;
                font-weight: bold;
                text-transform: uppercase;
            }
            
            .status-active {
                background: rgba(0, 255, 136, 0.2);
                color: #00ff88;
            }
            
            .status-pending {
                background: rgba(255, 193, 7, 0.2);
                color: #ffc107;
            }
            
            .status-suspended {
                background: rgba(255, 71, 87, 0.2);
                color: #ff4757;
            }
            
            .action-btn {
                padding: 8px 15px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.8em;
                font-weight: 600;
                margin: 0 5px;
                transition: all 0.3s ease;
            }
            
            .btn-approve {
                background: linear-gradient(45deg, #00ff88, #00cc6a);
                color: white;
            }
            
            .btn-suspend {
                background: linear-gradient(45deg, #ff4757, #ff3742);
                color: white;
            }
            
            .btn-activate {
                background: linear-gradient(45deg, #00d4ff, #0099cc);
                color: white;
            }
            
            .action-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            }
            
            .loading {
                text-align: center;
                padding: 40px;
                color: #a0a0a0;
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
            
            @media (max-width: 768px) {
                .header-content {
                    flex-direction: column;
                    gap: 20px;
                }
                
                .dashboard-grid {
                    grid-template-columns: 1fr;
                }
                
                .users-table {
                    padding: 20px;
                }
                
                table {
                    font-size: 0.9em;
                }
                
                th, td {
                    padding: 10px;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo">ThinkSync™ Admin Dashboard</div>
                <div class="user-info">
                    <span id="adminName">Loading...</span>
                    <button class="logout-btn" onclick="logout()">Logout</button>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div id="message"></div>
            
            <div class="dashboard-grid">
                <div class="card">
                    <div class="card-title">
                        👥 Total Users
                    </div>
                    <div class="stat-number" id="totalUsers">-</div>
                    <div class="stat-label">Registered clinicians</div>
                </div>
                
                <div class="card">
                    <div class="card-title">
                        ✅ Active Users
                    </div>
                    <div class="stat-number" id="activeUsers">-</div>
                    <div class="stat-label">Currently active</div>
                </div>
                
                <div class="card">
                    <div class="card-title">
                        ⏳ Pending Approval
                    </div>
                    <div class="stat-number" id="pendingUsers">-</div>
                    <div class="stat-label">Awaiting approval</div>
                </div>
                
                <div class="card">
                    <div class="card-title">
                        📊 Total Sessions
                    </div>
                    <div class="stat-number" id="totalSessions">-</div>
                    <div class="stat-label">Therapy sessions processed</div>
                </div>
            </div>
            
            <div class="users-table">
                <div class="table-header">User Management</div>
                <div id="usersLoading" class="loading">Loading users...</div>
                <div id="usersTable" style="display: none;">
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Email</th>
                                <th>License</th>
                                <th>State</th>
                                <th>Status</th>
                                <th>Registered</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="usersTableBody">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <script>
            let authToken = localStorage.getItem('thinksync_token');
            let currentUser = JSON.parse(localStorage.getItem('thinksync_user') || '{}');
            
            // Check authentication
            if (!authToken || currentUser.role !== 'admin') {
                window.location.href = '/api/auth/login-form';
            }
            
            document.getElementById('adminName').textContent = currentUser.full_name || 'Admin';
            
            // Load dashboard data
            async function loadDashboard() {
                try {
                    // Load statistics
                    const statsResponse = await fetch('/api/auth/admin/stats', {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });
                    
                    if (statsResponse.ok) {
                        const statsData = await statsResponse.json();
                        if (statsData.success) {
                            document.getElementById('totalUsers').textContent = statsData.stats.users.total;
                            document.getElementById('activeUsers').textContent = statsData.stats.users.active;
                            document.getElementById('pendingUsers').textContent = statsData.stats.users.pending;
                            document.getElementById('totalSessions').textContent = statsData.stats.sessions.total;
                        }
                    }
                    
                    // Load users
                    const usersResponse = await fetch('/api/auth/admin/users', {
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });
                    
                    if (usersResponse.ok) {
                        const usersData = await usersResponse.json();
                        if (usersData.success) {
                            displayUsers(usersData.users);
                        }
                    }
                    
                } catch (error) {
                    showMessage('Failed to load dashboard data', 'error');
                }
            }
            
            function displayUsers(users) {
                const tbody = document.getElementById('usersTableBody');
                tbody.innerHTML = '';
                
                users.forEach(user => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${user.full_name}</td>
                        <td>${user.email}</td>
                        <td>${user.license_type} ${user.license_number}</td>
                        <td>${user.state_of_licensure}</td>
                        <td><span class="status-badge status-${user.status}">${user.status}</span></td>
                        <td>${new Date(user.created_at).toLocaleDateString()}</td>
                        <td>
                            ${user.status === 'pending' ? 
                                `<button class="action-btn btn-approve" onclick="updateUserStatus(${user.id}, 'active')">Approve</button>` : ''}
                            ${user.status === 'active' ? 
                                `<button class="action-btn btn-suspend" onclick="updateUserStatus(${user.id}, 'suspended')">Suspend</button>` : ''}
                            ${user.status === 'suspended' ? 
                                `<button class="action-btn btn-activate" onclick="updateUserStatus(${user.id}, 'active')">Activate</button>` : ''}
                        </td>
                    `;
                    tbody.appendChild(row);
                });
                
                document.getElementById('usersLoading').style.display = 'none';
                document.getElementById('usersTable').style.display = 'block';
            }
            
            async function updateUserStatus(userId, newStatus) {
                try {
                    const response = await fetch(`/api/auth/admin/users/${userId}/status`, {
                        method: 'PUT',
                        headers: {
                            'Authorization': `Bearer ${authToken}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ status: newStatus })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        showMessage(`User status updated to ${newStatus}`, 'success');
                        loadDashboard(); // Reload data
                    } else {
                        showMessage(result.error, 'error');
                    }
                } catch (error) {
                    showMessage('Failed to update user status', 'error');
                }
            }
            
            function logout() {
                localStorage.removeItem('thinksync_token');
                localStorage.removeItem('thinksync_user');
                window.location.href = '/api/auth/login-form';
            }
            
            function showMessage(text, type) {
                const messageDiv = document.getElementById('message');
                messageDiv.innerHTML = `<div class="message ${type}">${text}</div>`;
                setTimeout(() => {
                    messageDiv.innerHTML = '';
                }, 5000);
            }
            
            // Load dashboard on page load
            loadDashboard();
            
            // Auto-refresh every 30 seconds
            setInterval(loadDashboard, 30000);
        </script>
    </body>
    </html>
    '''
    return render_template_string(dashboard_html)

