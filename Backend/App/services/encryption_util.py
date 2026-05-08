import os
from cryptography.fernet import Fernet

class SimpleEncryptor:
    def __init__(self, key: bytes = None):
        # 1. Prioritize explicitly passed key, fallback to Environment Variable
        raw_key = key or os.environ.get('APP_ENCRYPTION_KEY')
        
        # 2. Fail loudly if no key is found
        if not raw_key:
            raise ValueError("CRITICAL: APP_ENCRYPTION_KEY environment variable is not set.")
            
        # 3. Strip invisible characters/newlines that cause the 32-byte error
        raw_key = raw_key.strip() 
        
        # 4. Ensure the key is in bytes
        self.key = raw_key if isinstance(raw_key, bytes) else raw_key.encode('utf-8')
        self.cipher = Fernet(self.key)

    def encrypt(self, data: bytes) -> bytes:
        return self.cipher.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        return self.cipher.decrypt(token)