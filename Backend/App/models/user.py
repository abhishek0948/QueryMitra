from datetime import datetime
import uuid
import bcrypt

class User:
    def __init__(self, name, email, password_hash, user_id=None, created_at=None, role='user'):
        self.id = user_id or str(uuid.uuid4())
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.role = role  # 'user' or 'admin'
        self.created_at = created_at or datetime.utcnow()
        
    @staticmethod
    def hash_password(password):
        """Hash a password for storing."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verify a stored password against one provided by user."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def to_dict(self):
        """Convert user object to dictionary (without password)."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create User instance from dictionary."""
        return cls(
            name=data['name'],
            email=data['email'],
            password_hash=data['password_hash'],
            user_id=data.get('id'),
            created_at=data.get('created_at'),
            role=data.get('role', 'user')
        )
