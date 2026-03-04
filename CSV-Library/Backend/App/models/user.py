import uuid
from datetime import datetime


class User:
    def __init__(self, name: str, email: str, password_hash: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at.isoformat()
        }

    def to_public_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
        }
