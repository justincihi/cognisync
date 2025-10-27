"""
Data Retention and Deletion Policy for HIPAA Compliance
Implements automated data retention and secure deletion
"""

import os
import sqlite3
from datetime import datetime, timedelta
import logging
import shutil

logger = logging.getLogger(__name__)

class DataRetentionPolicy:
    """
    HIPAA-compliant data retention and deletion handler
    """
    
    def __init__(self, db_connection, retention_years=7):
        """
        Initialize data retention policy
        
        Args:
            db_connection: Database connection
            retention_years: Number of years to retain data (default 7 for HIPAA)
        """
        self.db = db_connection
        self.retention_years = retention_years
        self.retention_days = retention_years * 365
    
    def set_retention_date(self, session_id):
        """
        Set retention date for a therapy session
        
        Args:
            session_id: Session ID
            
        Returns:
            Retention date
        """
        retention_date = datetime.now() + timedelta(days=self.retention_days)
        
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                UPDATE therapy_sessions 
                SET retention_until = ? 
                WHERE session_id = ?
            ''', (retention_date, session_id))
            self.db.conn.commit()
            
            logger.info(f"📅 Set retention date for {session_id}: {retention_date.date()}")
            return retention_date
        except Exception as e:
            logger.error(f"Failed to set retention date: {e}")
            return None
    
    def get_expired_sessions(self):
        """
        Get list of sessions past their retention date
        
        Returns:
            List of session IDs to be deleted
        """
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT session_id, file_path_encrypted, client_name_encrypted 
                FROM therapy_sessions 
                WHERE retention_until < ? 
                AND retention_until IS NOT NULL
            ''', (datetime.now(),))
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to get expired sessions: {e}")
            return []
    
    def secure_delete_file(self, file_path):
        """
        Securely delete a file (overwrite before deletion)
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            Boolean indicating success
        """
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return False
        
        try:
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Overwrite with random data 3 times (DoD 5220.22-M standard)
            for i in range(3):
                with open(file_path, 'wb') as f:
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # Delete file
            os.remove(file_path)
            
            logger.info(f"🗑️  Securely deleted file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to securely delete file: {e}")
            return False
    
    def delete_session(self, session_id, audit_logger=None, user_id=None, username=None):
        """
        Delete a therapy session and associated files
        
        Args:
            session_id: Session ID to delete
            audit_logger: Audit logger instance
            user_id: User performing deletion
            username: Username performing deletion
            
        Returns:
            Boolean indicating success
        """
        try:
            # Get session details
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT file_path_encrypted, client_name_encrypted 
                FROM therapy_sessions 
                WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Session not found: {session_id}")
                return False
            
            # Decrypt file path if encrypted
            file_path_encrypted = row[0] if isinstance(row, tuple) else row['file_path_encrypted']
            
            if file_path_encrypted:
                # Decrypt if needed
                if hasattr(self.db, 'decrypt_field'):
                    file_path = self.db.decrypt_field(file_path_encrypted)
                else:
                    file_path = file_path_encrypted
                
                # Securely delete file
                if file_path:
                    self.secure_delete_file(file_path)
            
            # Delete database record
            cursor.execute('''
                DELETE FROM therapy_sessions 
                WHERE session_id = ?
            ''', (session_id,))
            
            self.db.conn.commit()
            
            # Log deletion
            if audit_logger:
                audit_logger.log_data_deletion(
                    user_id=user_id,
                    username=username,
                    resource_type='therapy_session',
                    resource_id=session_id
                )
            
            logger.info(f"✅ Deleted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    def run_retention_cleanup(self, audit_logger=None, dry_run=False):
        """
        Run automated retention cleanup
        
        Args:
            audit_logger: Audit logger instance
            dry_run: If True, only report what would be deleted
            
        Returns:
            Number of sessions deleted
        """
        expired_sessions = self.get_expired_sessions()
        
        if not expired_sessions:
            logger.info("✅ No expired sessions to delete")
            return 0
        
        logger.info(f"📋 Found {len(expired_sessions)} expired sessions")
        
        if dry_run:
            logger.info("🔍 DRY RUN - No data will be deleted")
            for session in expired_sessions:
                logger.info(f"  Would delete: {session['session_id']}")
            return 0
        
        deleted_count = 0
        for session in expired_sessions:
            success = self.delete_session(
                session['session_id'],
                audit_logger=audit_logger,
                user_id=0,  # System user
                username='system_retention_policy'
            )
            if success:
                deleted_count += 1
        
        logger.info(f"✅ Deleted {deleted_count} expired sessions")
        return deleted_count
    
    def get_retention_stats(self):
        """
        Get statistics about data retention
        
        Returns:
            Dictionary with retention statistics
        """
        try:
            cursor = self.db.conn.cursor()
            
            # Total sessions
            cursor.execute('SELECT COUNT(*) FROM therapy_sessions')
            total_sessions = cursor.fetchone()[0]
            
            # Sessions with retention date set
            cursor.execute('SELECT COUNT(*) FROM therapy_sessions WHERE retention_until IS NOT NULL')
            sessions_with_retention = cursor.fetchone()[0]
            
            # Expired sessions
            cursor.execute('SELECT COUNT(*) FROM therapy_sessions WHERE retention_until < ?', (datetime.now(),))
            expired_sessions = cursor.fetchone()[0]
            
            # Sessions expiring in next 30 days
            future_date = datetime.now() + timedelta(days=30)
            cursor.execute('''
                SELECT COUNT(*) FROM therapy_sessions 
                WHERE retention_until BETWEEN ? AND ?
            ''', (datetime.now(), future_date))
            expiring_soon = cursor.fetchone()[0]
            
            return {
                'total_sessions': total_sessions,
                'sessions_with_retention': sessions_with_retention,
                'expired_sessions': expired_sessions,
                'expiring_in_30_days': expiring_soon,
                'retention_years': self.retention_years
            }
        except Exception as e:
            logger.error(f"Failed to get retention stats: {e}")
            return {}


if __name__ == "__main__":
    # Test data retention
    print("Testing Data Retention Policy...")
    
    # Create test database
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE therapy_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            client_name_encrypted TEXT,
            file_path_encrypted TEXT,
            retention_until TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert test data
    test_sessions = [
        ('session_1', 'uploads/session_1.mp3', datetime.now() + timedelta(days=365)),
        ('session_2', 'uploads/session_2.mp3', datetime.now() - timedelta(days=1)),  # Expired
        ('session_3', 'uploads/session_3.mp3', datetime.now() + timedelta(days=10)),
    ]
    
    for session_id, file_path, retention_date in test_sessions:
        cursor.execute('''
            INSERT INTO therapy_sessions (session_id, file_path_encrypted, retention_until)
            VALUES (?, ?, ?)
        ''', (session_id, file_path, retention_date))
    
    conn.commit()
    
    # Create mock database object
    class MockDB:
        def __init__(self, conn):
            self.conn = conn
    
    db = MockDB(conn)
    retention = DataRetentionPolicy(db, retention_years=7)
    
    # Get stats
    stats = retention.get_retention_stats()
    print(f"\n📊 Retention Statistics:")
    print(f"  Total sessions: {stats['total_sessions']}")
    print(f"  With retention date: {stats['sessions_with_retention']}")
    print(f"  Expired: {stats['expired_sessions']}")
    print(f"  Expiring in 30 days: {stats['expiring_in_30_days']}")
    
    # Get expired sessions
    expired = retention.get_expired_sessions()
    print(f"\n🗑️  Expired sessions: {len(expired)}")
    for session in expired:
        print(f"  - {session['session_id']}")
    
    # Dry run cleanup
    print("\n🔍 Running dry run cleanup...")
    count = retention.run_retention_cleanup(dry_run=True)
    
    print("\n✅ Data retention test complete!")

