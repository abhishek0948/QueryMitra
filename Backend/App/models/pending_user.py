from datetime import datetime
import uuid

class PendingUser:
    """Temporary storage for unverified users"""
    def __init__(self, name, email, password_hash, user_id=None, created_at=None):
        self.id = user_id or str(uuid.uuid4())
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at or datetime.utcnow()
        self.verified = False
        
    def to_dict(self):
        """Convert pending user object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'verified': self.verified
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create PendingUser instance from dictionary."""
        return cls(
            name=data['name'],
            email=data['email'],
            password_hash=data['password_hash'],
            user_id=data.get('id'),
            created_at=data.get('created_at')
        )
