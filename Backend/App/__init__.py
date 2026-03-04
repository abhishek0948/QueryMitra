from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from pymongo import MongoClient
from config import Config
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Disable strict slashes to prevent redirects
    app.url_map.strict_slashes = False
    
    # Validate configuration
    Config.validate_config()
    
    # Enable CORS with proper configuration for JWT authentication
    CORS(app, 
         origins=["http://localhost:3000", "http://localhost:5173"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"],
         supports_credentials=True,
         expose_headers=["Content-Type", "Authorization"])
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Initialize Flask-Mail
    mail = Mail(app)
    
    # Initialize MongoDB connection with error handling
    try:
        # For MongoDB Atlas connections with SSL
        client = MongoClient(
            app.config['MONGODB_URI'],
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=30000,
            socketTimeoutMS=None,
            connect=True,
            retryWrites=True,
            w="majority"
        )
        # Test the connection
        client.admin.command('ping')
        app.db = client[app.config['DATABASE_NAME']]
        print("✅ MongoDB Atlas connection successful")
    except Exception as e:
        print(f"MongoDB Atlas connection error: {str(e)}")
        print("Attempting to connect to local MongoDB...")
        
        # Try local MongoDB as first fallback
        try:
            client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000)
            client.admin.command('ping')
            app.db = client[app.config['DATABASE_NAME']]
            print("✅ Local MongoDB connection successful")
        except Exception as local_e:
            print(f"Local MongoDB connection error: {str(local_e)}")
            
            # Create a fallback in-memory database for testing
            try:
                from pymongo_inmemory import MongoClient as InMemoryMongoClient
                client = InMemoryMongoClient()
                app.db = client[app.config['DATABASE_NAME']]
                print("✅ Using in-memory MongoDB fallback")
            except Exception as inner_e:
                print(f"Failed to create in-memory MongoDB: {str(inner_e)}")
                # Create a simple dictionary-based fallback if all else fails
                app.db = {"datasets": []}
                print("⚠️  Using simple dictionary fallback for database")
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints - import here, not at the top
    from App.routes import dataset_routes, query_routes, auth_routes, admin_routes
    app.register_blueprint(dataset_routes.bp)
    app.register_blueprint(query_routes.bp)
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(admin_routes.bp)
    
    # Initialize admin user after blueprints are registered
    with app.app_context():
        from App.services.auth_service import AuthService
        auth_service = AuthService()
        auth_service.initialize_admin()
    
    # Add health check route
    @app.route('/api/health')
    def health_check():
        gemini_status = "✅ Configured" if app.config.get('GEMINI_API_KEY') else "❌ Not configured"
        return {
            'status': 'healthy',
            'database': 'connected' if hasattr(app, 'db') else 'disconnected',
            'gemini_api': gemini_status
        }
    
    return app