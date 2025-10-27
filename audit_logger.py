"""
Comprehensive Audit Logging for HIPAA Compliance
Logs all PHI access and system actions
"""

import sqlite3
from datetime import datetime
import json
import logging
from functools import wraps
from flask import request, g

logger = logging.getLogger(__name__)

class AuditLogger:
    """
    HIPAA-compliant audit logging system
    """
    
    def __init__(self, db_connection):
        """
        Initialize audit logger
        
        Args:
            db_connection: Database connection object
        """
        self.db = db_connection
    
    def log_action(self, action, resource_type=None, resource_id=None, 
                   user_id=None, username=None, success=True, details=None):
        """
        Log an action to the audit trail
        
        Args:
            action: Action performed (e.g., 'login', 'view_session', 'create_session')
            resource_type: Type of resource accessed (e.g., 'therapy_session', 'user')
            resource_id: ID of resource accessed
            user_id: ID of user performing action
            username: Username of user
            success: Whether action was successful
            details: Additional details as dict
        """
        try:
            # Get request context if available
            ip_address = None
            user_agent = None
            
            try:
                if request:
                    ip_address = request.remote_addr
                    user_agent = request.headers.get('User-Agent', '')
            except:
                pass
            
            # Encrypt sensitive details
            details_json = json.dumps(details) if details else None
            if details_json and hasattr(self.db, 'encrypt_field'):
                details_encrypted = self.db.encrypt_field(details_json)
            else:
                details_encrypted = details_json
            
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO audit_log 
                (user_id, username, action, resource_type, resource_id, 
                 ip_address, user_agent, success, details_encrypted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, action, resource_type, resource_id,
                  ip_address, user_agent, success, details_encrypted))
            
            self.db.conn.commit()
            
            logger.info(f"📋 Audit: {username or 'Unknown'} - {action} - {resource_type}:{resource_id} - {'✅' if success else '❌'}")
            
        except Exception as e:
            logger.error(f"❌ Audit logging failed: {e}")
            # Don't raise - audit failure shouldn't break the app
    
    def log_phi_access(self, user_id, username, session_id, action='view'):
        """
        Log PHI (Protected Health Information) access
        
        Args:
            user_id: ID of user accessing PHI
            username: Username
            session_id: Therapy session ID
            action: Type of access (view, edit, delete, export)
        """
        self.log_action(
            action=f'phi_{action}',
            resource_type='therapy_session',
            resource_id=session_id,
            user_id=user_id,
            username=username,
            success=True,
            details={'phi_accessed': True, 'session_id': session_id}
        )
    
    def log_login(self, username, success, reason=None):
        """
        Log login attempt
        
        Args:
            username: Username attempting login
            success: Whether login was successful
            reason: Reason for failure (if applicable)
        """
        self.log_action(
            action='login',
            username=username,
            success=success,
            details={'reason': reason} if reason else None
        )
    
    def log_logout(self, user_id, username):
        """
        Log logout
        
        Args:
            user_id: User ID
            username: Username
        """
        self.log_action(
            action='logout',
            user_id=user_id,
            username=username,
            success=True
        )
    
    def log_data_export(self, user_id, username, session_id, export_format):
        """
        Log data export
        
        Args:
            user_id: User ID
            username: Username
            session_id: Session ID being exported
            export_format: Format of export (pdf, docx, json, etc.)
        """
        self.log_action(
            action='export_data',
            resource_type='therapy_session',
            resource_id=session_id,
            user_id=user_id,
            username=username,
            success=True,
            details={'export_format': export_format}
        )
    
    def log_data_deletion(self, user_id, username, resource_type, resource_id):
        """
        Log data deletion
        
        Args:
            user_id: User ID
            username: Username
            resource_type: Type of resource deleted
            resource_id: ID of resource deleted
        """
        self.log_action(
            action='delete_data',
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            username=username,
            success=True,
            details={'permanent_deletion': True}
        )
    
    def get_audit_trail(self, user_id=None, resource_id=None, action=None, 
                       start_date=None, end_date=None, limit=100):
        """
        Retrieve audit trail
        
        Args:
            user_id: Filter by user ID
            resource_id: Filter by resource ID
            action: Filter by action type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of records
            
        Returns:
            List of audit log entries
        """
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if resource_id:
            query += " AND resource_id = ?"
            params.append(resource_id)
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = self.db.conn.cursor()
        cursor.execute(query, params)
        
        return [dict(row) for row in cursor.fetchall()]


def audit_log(action, resource_type=None):
    """
    Decorator for automatic audit logging
    
    Usage:
        @audit_log('create_session', 'therapy_session')
        def create_session():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute function
            result = f(*args, **kwargs)
            
            # Log action
            try:
                if hasattr(g, 'audit_logger') and hasattr(g, 'current_user'):
                    g.audit_logger.log_action(
                        action=action,
                        resource_type=resource_type,
                        user_id=g.current_user.get('id'),
                        username=g.current_user.get('username'),
                        success=True
                    )
            except Exception as e:
                logger.error(f"Audit logging failed: {e}")
            
            return result
        return decorated_function
    return decorator


if __name__ == "__main__":
    # Test audit logging
    print("Testing audit logging...")
    
    # Create test database
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            username TEXT,
            action TEXT NOT NULL,
            resource_type TEXT,
            resource_id TEXT,
            ip_address TEXT,
            user_agent TEXT,
            success BOOLEAN,
            details_encrypted TEXT
        )
    ''')
    
    # Create mock database object
    class MockDB:
        def __init__(self, conn):
            self.conn = conn
    
    db = MockDB(conn)
    audit = AuditLogger(db)
    
    # Test logging
    audit.log_login('testuser', True)
    audit.log_phi_access(1, 'testuser', 'session_123', 'view')
    audit.log_data_export(1, 'testuser', 'session_123', 'pdf')
    audit.log_logout(1, 'testuser')
    
    # Retrieve audit trail
    trail = audit.get_audit_trail()
    
    print(f"\n✅ Logged {len(trail)} audit entries:")
    for entry in trail:
        print(f"  - {entry['timestamp']}: {entry['username']} - {entry['action']}")
    
    print("\n✅ Audit logging test complete!")

