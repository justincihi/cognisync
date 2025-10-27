"""
File Encryption Module for HIPAA Compliance
Encrypts audio files and other PHI files using AES-256
"""

import os
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import logging

logger = logging.getLogger(__name__)

class FileEncryption:
    """
    HIPAA-compliant file encryption handler
    Uses AES-256 encryption for files
    """
    
    def __init__(self, encryption_key=None):
        """
        Initialize file encryption
        
        Args:
            encryption_key: Encryption key (will use environment variable if not provided)
        """
        if encryption_key:
            self.encryption_key = encryption_key
        else:
            self.encryption_key = os.environ.get('FILE_ENCRYPTION_KEY')
            if not self.encryption_key:
                # Generate new key
                self.encryption_key = Fernet.generate_key().decode()
                logger.warning("⚠️  Generated new file encryption key - STORE THIS SECURELY!")
                logger.warning(f"FILE_ENCRYPTION_KEY={self.encryption_key}")
        
        # Derive 32-byte key for AES-256
        self.aes_key = hashlib.sha256(self.encryption_key.encode()).digest()
    
    def encrypt_file(self, input_path, output_path=None):
        """
        Encrypt a file using AES-256
        
        Args:
            input_path: Path to file to encrypt
            output_path: Path for encrypted file (defaults to input_path + '.encrypted')
            
        Returns:
            Path to encrypted file
        """
        if output_path is None:
            output_path = input_path + '.encrypted'
        
        try:
            # Generate random IV
            iv = os.urandom(16)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.aes_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Read and encrypt file
            with open(input_path, 'rb') as f_in:
                plaintext = f_in.read()
            
            # Add padding
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(plaintext) + padder.finalize()
            
            # Encrypt
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            
            # Write IV + ciphertext
            with open(output_path, 'wb') as f_out:
                f_out.write(iv + ciphertext)
            
            logger.info(f"✅ File encrypted: {input_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ File encryption failed: {e}")
            raise
    
    def decrypt_file(self, input_path, output_path=None):
        """
        Decrypt a file
        
        Args:
            input_path: Path to encrypted file
            output_path: Path for decrypted file (defaults to input_path without '.encrypted')
            
        Returns:
            Path to decrypted file
        """
        if output_path is None:
            if input_path.endswith('.encrypted'):
                output_path = input_path[:-10]  # Remove '.encrypted'
            else:
                output_path = input_path + '.decrypted'
        
        try:
            # Read encrypted file
            with open(input_path, 'rb') as f_in:
                data = f_in.read()
            
            # Extract IV and ciphertext
            iv = data[:16]
            ciphertext = data[16:]
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.aes_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remove padding
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_data) + unpadder.finalize()
            
            # Write decrypted file
            with open(output_path, 'wb') as f_out:
                f_out.write(plaintext)
            
            logger.info(f"✅ File decrypted: {input_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ File decryption failed: {e}")
            raise
    
    def encrypt_and_replace(self, file_path):
        """
        Encrypt a file and replace the original
        
        Args:
            file_path: Path to file
            
        Returns:
            Path to encrypted file
        """
        encrypted_path = self.encrypt_file(file_path)
        
        # Remove original file
        os.remove(file_path)
        
        # Rename encrypted file to original name
        os.rename(encrypted_path, file_path)
        
        logger.info(f"✅ File encrypted in place: {file_path}")
        return file_path
    
    def get_file_hash(self, file_path):
        """
        Calculate SHA-256 hash of file for integrity verification
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex string of file hash
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


def get_file_encryption_key():
    """
    Get or generate file encryption key
    
    Returns:
        Encryption key as string
    """
    key = os.environ.get('FILE_ENCRYPTION_KEY')
    if not key:
        # Generate new key
        key = Fernet.generate_key().decode()
        print(f"\n⚠️  IMPORTANT: Store this file encryption key securely!")
        print(f"Add to your environment variables:")
        print(f"export FILE_ENCRYPTION_KEY='{key}'")
        print()
    return key


if __name__ == "__main__":
    # Test file encryption
    print("Testing file encryption...")
    
    # Create test file
    test_file = "/tmp/test_audio.txt"
    with open(test_file, 'w') as f:
        f.write("This is a test therapy session recording with PHI data.")
    
    key = get_file_encryption_key()
    encryptor = FileEncryption(encryption_key=key)
    
    # Test encryption
    print(f"\nOriginal file: {test_file}")
    print(f"Original hash: {encryptor.get_file_hash(test_file)}")
    
    encrypted_file = encryptor.encrypt_file(test_file)
    print(f"\nEncrypted file: {encrypted_file}")
    print(f"Encrypted hash: {encryptor.get_file_hash(encrypted_file)}")
    
    # Test decryption
    decrypted_file = encryptor.decrypt_file(encrypted_file)
    print(f"\nDecrypted file: {decrypted_file}")
    print(f"Decrypted hash: {encryptor.get_file_hash(decrypted_file)}")
    
    # Verify content
    with open(decrypted_file, 'r') as f:
        content = f.read()
    print(f"\nDecrypted content: {content}")
    
    # Cleanup
    os.remove(test_file)
    os.remove(encrypted_file)
    os.remove(decrypted_file)
    
    print("\n✅ File encryption test complete!")

