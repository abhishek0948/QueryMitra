import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'csv-library-secret-2024')
    MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'csv_library')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'csv-library-jwt-secret-2024')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB max upload
