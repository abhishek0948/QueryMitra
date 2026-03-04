import uuid
from datetime import datetime
from typing import List


class CSVFile:
    def __init__(
        self,
        name: str,
        description: str,
        filename: str,
        uploader_id: str,
        uploader_name: str,
        row_count: int,
        columns: List[str],
        file_size: int,
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.filename = filename
        self.uploader_id = uploader_id
        self.uploader_name = uploader_name
        self.row_count = row_count
        self.columns = columns
        self.file_size = file_size
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'filename': self.filename,
            'uploader_id': self.uploader_id,
            'uploader_name': self.uploader_name,
            'row_count': self.row_count,
            'columns': self.columns,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat(),
        }
