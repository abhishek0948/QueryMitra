from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from config import Config
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.url_map.strict_slashes = False

    CORS(app,
         origins=["http://localhost:5174", "http://localhost:3000", "http://127.0.0.1:5174"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"],
         supports_credentials=True)

    JWTManager(app)

    # MongoDB connection
    try:
        client = MongoClient(app.config['MONGODB_URI'], serverSelectionTimeoutMS=4000)
        client.admin.command('ping')
        app.db = client[app.config['DATABASE_NAME']]
        print("✅ MongoDB connected")
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {e}")
        # Fallback: try local
        try:
            client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000)
            client.admin.command('ping')
            app.db = client[app.config['DATABASE_NAME']]
            print("✅ Local MongoDB connected")
        except Exception as le:
            print(f"❌ All MongoDB connections failed: {le}")
            app.db = None

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from App.routes import auth_routes, csv_routes
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(csv_routes.bp)

    @app.route('/api/health')
    def health():
        return {
            'status': 'ok',
            'db': 'connected' if app.db is not None else 'disconnected'
        }

    return app
