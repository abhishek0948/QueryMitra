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
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    
    # Email Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'lodhesuraj2006@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'pwyr esha dban ymht')  # Replace with App Password from Google
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'lodhesuraj2006@gmail.com')
    
    # OTP Configuration
    OTP_EXPIRY_MINUTES = 5  # OTP valid for 5 minutes
    
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