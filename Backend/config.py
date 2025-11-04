import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # MongoDB Atlas connection string
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://kartikeylodhe:LMpIhkg0n4quYPS0@cluster0.hudluyw.mongodb.net/query_mitra?retryWrites=true&w=majority')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'query_mitra')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Google Generative AI (Gemini) API Key
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Validate that required environment variables are set
    @classmethod
    def validate_config(cls):
        required_vars = ['MONGODB_URI', 'GEMINI_API_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
            if 'GEMINI_API_KEY' in missing_vars:
                print("Natural Language queries will not work without GEMINI_API_KEY")
        else:
            print("✅ All required environment variables are configured")