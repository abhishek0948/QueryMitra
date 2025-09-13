import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MongoDB Atlas connection string
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://kartikeylodhe:kartikey1234@cluster0.hudluyw.mongodb.net/query_mitra?retryWrites=true&w=majority')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'query_mitra')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    # Google Generative AI (Gemini) API Key
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyC4kL3ZkdeQJ7nhbrRmLvSM3Eg9hNKCvVU')