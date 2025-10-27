"""
Encrypted Database Module for HIPAA Compliance
Uses SQLCipher for encrypted SQLite database
"""

import os
import sqlite3
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import logging

logger = logging.getLogger(__name__)

class EncryptedDatabase:
    """
    HIPAA-compliant encrypted database handler
    """
    
    def __init__(self, db_path='cognisync_encrypted.db', encryption_key=None):
        """
        Initialize encrypted database
        
        Args:
            db_path: Path to database file
            encryption_key: Encryption key (will generate if not provided)
        """
        self.db_path = db_path
        
        # Get or generate encryption key
        if encryption_key:
            self.encryption_key = encryption_key
        else:
            self.encryption_key = os.environ.get('DB_ENCRYPTION_KEY')
            if not self.encryption_key:
                # Generate new key (store this securely!)
                self.encryption_key = Fernet.generate_key().decode()
                logger.warning("⚠️  Generated new encryption key - STORE THIS SECURELY!")
                logger.warning(f"DB_ENCRYPTION_KEY={self.encryption_key}")
        
        self.fernet = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)
        self.conn = None
        
    def connect(self):
        """Connect to database"""
        try:
            # Try to use pysqlcipher3 for full database encryption
            try:
                from pysqlcipher3 import dbapi2 as sqlcipher
                self.conn = sqlcipher.connect(self.db_path)
                # Set encryption key for SQLCipher
                self.conn.execute(f"PRAGMA key = '{self.encryption_key}'")
                logger.info("✅ Connected to encrypted database (SQLCipher)")
            except ImportError:
                # Fallback to regular SQLite with field-level encryption
                self.conn = sqlite3.connect(self.db_path)
                logger.warning("⚠️  SQLCipher not available, using field-level encryption")
            
            self.conn.row_factory = sqlite3.Row
            return self.conn
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def encrypt_field(self, data):
        """
        Encrypt a single field
        
        Args:
            data: String or bytes to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        if data is None:
            return None
        
        if isinstance(data, str):
            data = data.encode()
        
        encrypted = self.fernet.encrypt(data)
        return base64.b64encode(encrypted).decode()
    
    def decrypt_field(self, encrypted_data):
        """
        Decrypt a single field
        
        Args:
            encrypted_data: Base64 encoded encrypted string
            
        Returns:
            Decrypted string
        """
        if encrypted_data is None:
            return None
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"❌ Decryption failed: {e}")
            return None
    
    def create_tables(self):
        """Create database tables with encryption support"""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email_encrypted TEXT,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'clinician',
                license_number_encrypted TEXT,
                license_state TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_approved BOOLEAN DEFAULT 0,
                mfa_secret_encrypted TEXT,
                mfa_enabled BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_login_attempts INTEGER DEFAULT 0,
                account_locked_until TIMESTAMP
            )
        ''')
        
        # Therapy sessions table with encrypted PHI
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS therapy_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                client_name_encrypted TEXT NOT NULL,
                therapy_type TEXT,
                summary_format TEXT,
                file_path_encrypted TEXT,
                file_name_encrypted TEXT,
                file_size INTEGER,
                transcript_encrypted TEXT,
                clinical_notes_encrypted TEXT,
                sentiment_analysis_encrypted TEXT,
                patterns_encrypted TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                retention_until TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Audit log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
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
                details_encrypted TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Session tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                is_valid BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        self.conn.commit()
        logger.info("✅ Encrypted database tables created")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


def get_encryption_key():
    """
    Get or generate database encryption key
    
    Returns:
        Encryption key as string
    """
    key = os.environ.get('DB_ENCRYPTION_KEY')
    if not key:
        # Generate new key
        key = Fernet.generate_key().decode()
        print(f"\n⚠️  IMPORTANT: Store this encryption key securely!")
        print(f"Add to your environment variables:")
        print(f"export DB_ENCRYPTION_KEY='{key}'")
        print()
    return key


if __name__ == "__main__":
    # Test encryption
    print("Testing encrypted database...")
    
    key = get_encryption_key()
    db = EncryptedDatabase(encryption_key=key)
    db.connect()
    db.create_tables()
    
    # Test field encryption
    test_data = "Patient Name: John Doe"
    encrypted = db.encrypt_field(test_data)
    decrypted = db.decrypt_field(encrypted)
    
    print(f"Original: {test_data}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
    print(f"Match: {test_data == decrypted}")
    
    db.close()
    print("\n✅ Encryption test complete!")

