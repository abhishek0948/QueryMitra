from datetime import datetime
import uuid

class Dataset:
    def __init__(self, name, description, filename, schema, user_id=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.filename = filename
        self.schema = schema
        self.user_id = user_id  # Associate dataset with user
        self.created_at = datetime.utcnow()
        
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'filename': self.filename,
            'schema': self.schema,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat()
        }