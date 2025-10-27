"""
Multi-Factor Authentication (MFA) Module for HIPAA Compliance
Implements TOTP (Time-based One-Time Password) authentication
"""

import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MFAAuth:
    """
    Multi-Factor Authentication handler using TOTP
    """
    
    def __init__(self, issuer_name="CogniSync"):
        """
        Initialize MFA authentication
        
        Args:
            issuer_name: Name of the application for QR codes
        """
        self.issuer_name = issuer_name
    
    def generate_secret(self):
        """
        Generate a new MFA secret for a user
        
        Returns:
            Base32 encoded secret string
        """
        return pyotp.random_base32()
    
    def get_totp_uri(self, secret, username):
        """
        Generate TOTP URI for QR code
        
        Args:
            secret: User's MFA secret
            username: Username/email
            
        Returns:
            TOTP URI string
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=username,
            issuer_name=self.issuer_name
        )
    
    def generate_qr_code(self, secret, username):
        """
        Generate QR code image for MFA setup
        
        Args:
            secret: User's MFA secret
            username: Username/email
            
        Returns:
            Base64 encoded PNG image
        """
        uri = self.get_totp_uri(secret, username)
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_token(self, secret, token):
        """
        Verify a TOTP token
        
        Args:
            secret: User's MFA secret
            token: 6-digit token from authenticator app
            
        Returns:
            Boolean indicating if token is valid
        """
        if not secret or not token:
            return False
        
        try:
            totp = pyotp.TOTP(secret)
            # Allow 1 time step before and after for clock drift
            return totp.verify(token, valid_window=1)
        except Exception as e:
            logger.error(f"MFA verification failed: {e}")
            return False
    
    def get_current_token(self, secret):
        """
        Get current valid token (for testing only!)
        
        Args:
            secret: User's MFA secret
            
        Returns:
            Current 6-digit token
        """
        totp = pyotp.TOTP(secret)
        return totp.now()
    
    def generate_backup_codes(self, count=10):
        """
        Generate backup codes for account recovery
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = pyotp.random_base32()[:8]
            codes.append(code)
        return codes


class SessionTimeout:
    """
    Automatic session timeout for HIPAA compliance
    """
    
    def __init__(self, timeout_minutes=15):
        """
        Initialize session timeout handler
        
        Args:
            timeout_minutes: Minutes of inactivity before timeout
        """
        self.timeout_minutes = timeout_minutes
        self.timeout_seconds = timeout_minutes * 60
    
    def is_session_expired(self, last_activity):
        """
        Check if session has expired
        
        Args:
            last_activity: Datetime of last activity
            
        Returns:
            Boolean indicating if session is expired
        """
        if not last_activity:
            return True
        
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity)
        
        timeout_threshold = datetime.now() - timedelta(seconds=self.timeout_seconds)
        return last_activity < timeout_threshold
    
    def get_remaining_time(self, last_activity):
        """
        Get remaining time before session expires
        
        Args:
            last_activity: Datetime of last activity
            
        Returns:
            Remaining seconds (0 if expired)
        """
        if not last_activity:
            return 0
        
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity)
        
        elapsed = (datetime.now() - last_activity).total_seconds()
        remaining = max(0, self.timeout_seconds - elapsed)
        return int(remaining)
    
    def update_activity(self, db, token_hash):
        """
        Update last activity timestamp for a session
        
        Args:
            db: Database connection
            token_hash: Session token hash
        """
        try:
            cursor = db.conn.cursor()
            cursor.execute('''
                UPDATE session_tokens 
                SET last_activity = CURRENT_TIMESTAMP 
                WHERE token_hash = ? AND is_valid = 1
            ''', (token_hash,))
            db.conn.commit()
        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")
    
    def invalidate_expired_sessions(self, db):
        """
        Invalidate all expired sessions
        
        Args:
            db: Database connection
            
        Returns:
            Number of sessions invalidated
        """
        try:
            cursor = db.conn.cursor()
            
            # Calculate timeout threshold
            timeout_threshold = datetime.now() - timedelta(seconds=self.timeout_seconds)
            
            # Invalidate expired sessions
            cursor.execute('''
                UPDATE session_tokens 
                SET is_valid = 0 
                WHERE last_activity < ? AND is_valid = 1
            ''', (timeout_threshold,))
            
            count = cursor.rowcount
            db.conn.commit()
            
            if count > 0:
                logger.info(f"🔒 Invalidated {count} expired sessions")
            
            return count
        except Exception as e:
            logger.error(f"Failed to invalidate expired sessions: {e}")
            return 0


if __name__ == "__main__":
    # Test MFA
    print("Testing Multi-Factor Authentication...")
    
    mfa = MFAAuth()
    
    # Generate secret
    secret = mfa.generate_secret()
    print(f"\nMFA Secret: {secret}")
    
    # Generate QR code
    username = "testuser@example.com"
    qr_code = mfa.generate_qr_code(secret, username)
    print(f"\nQR Code generated (base64 length: {len(qr_code)})")
    
    # Get current token
    current_token = mfa.get_current_token(secret)
    print(f"\nCurrent Token: {current_token}")
    
    # Verify token
    is_valid = mfa.verify_token(secret, current_token)
    print(f"Token Valid: {is_valid}")
    
    # Test invalid token
    is_valid = mfa.verify_token(secret, "000000")
    print(f"Invalid Token Valid: {is_valid}")
    
    # Generate backup codes
    backup_codes = mfa.generate_backup_codes(5)
    print(f"\nBackup Codes: {backup_codes}")
    
    # Test session timeout
    print("\n\nTesting Session Timeout...")
    timeout = SessionTimeout(timeout_minutes=15)
    
    # Test with recent activity
    recent = datetime.now() - timedelta(minutes=5)
    print(f"\nLast activity 5 minutes ago:")
    print(f"  Expired: {timeout.is_session_expired(recent)}")
    print(f"  Remaining: {timeout.get_remaining_time(recent)} seconds")
    
    # Test with old activity
    old = datetime.now() - timedelta(minutes=20)
    print(f"\nLast activity 20 minutes ago:")
    print(f"  Expired: {timeout.is_session_expired(old)}")
    print(f"  Remaining: {timeout.get_remaining_time(old)} seconds")
    
    print("\n✅ MFA and session timeout tests complete!")

