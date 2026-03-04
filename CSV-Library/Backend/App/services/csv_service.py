import os
import pandas as pd
from flask import current_app
from App.models.csv_file import CSVFile


class CSVService:
    def __init__(self):
        self.db = current_app.db
        self.upload_folder = current_app.config['UPLOAD_FOLDER']

    def create(self, file_path: str, name: str, description: str,
               uploader_id: str, uploader_name: str) -> dict:
        df = pd.read_csv(file_path)
        row_count = len(df)
        columns = list(df.columns)
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)

        csv_file = CSVFile(
            name=name,
            description=description,
            filename=filename,
            uploader_id=uploader_id,
            uploader_name=uploader_name,
            row_count=row_count,
            columns=columns,
            file_size=file_size,
        )
        doc = csv_file.to_dict()
        self.db.csv_files.insert_one(doc)
        return doc

    def get_all(self) -> list:
        docs = list(self.db.csv_files.find({}, {'_id': 0}))
        docs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return docs

    def get_by_id(self, csv_id: str) -> dict | None:
        return self.db.csv_files.find_one({'id': csv_id}, {'_id': 0})

    def preview(self, csv_id: str, num_rows: int = 20) -> dict | None:
        doc = self.get_by_id(csv_id)
        if not doc:
            return None

        file_path = os.path.join(self.upload_folder, doc['filename'])
        if not os.path.exists(file_path):
            return None

        df = pd.read_csv(file_path, nrows=num_rows)
        return {
            'columns': list(df.columns),
            'rows': df.fillna('').to_dict('records'),
            'total_rows': doc['row_count'],
            'preview_count': len(df),
        }

    def get_file_path(self, csv_id: str) -> tuple[str | None, str | None]:
        doc = self.get_by_id(csv_id)
        if not doc:
            return None, None
        file_path = os.path.join(self.upload_folder, doc['filename'])
        return file_path, doc['filename']

    def delete(self, csv_id: str, user_id: str) -> tuple[bool, str]:
        doc = self.get_by_id(csv_id)
        if not doc:
            return False, 'CSV not found'
        if doc['uploader_id'] != user_id:
            return False, 'Unauthorized – only the uploader can delete this file'

        file_path = os.path.join(self.upload_folder, doc['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)

        self.db.csv_files.delete_one({'id': csv_id})
        return True, 'Deleted successfully'
