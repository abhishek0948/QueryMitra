from datetime import datetime
import uuid

class Dataset:
    def __init__(self, name, description, filename, schema):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.filename = filename
        self.schema = schema
        self.created_at = datetime.utcnow()
        
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'schema': self.schema,
            'created_at': self.created_at.isoformat()
        }