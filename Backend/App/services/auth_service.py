from flask import current_app
from App.models.user import User
from datetime import datetime

class AuthService:
    def __init__(self):
        self.db = current_app.db
        self.users_collection = self.db['users']
    
    def register_user(self, name, email, password):
        """Register a new user."""
        # Check if user already exists
        existing_user = self.users_collection.find_one({'email': email})
        if existing_user:
            raise ValueError('User with this email already exists')
        
        # Create new user with hashed password
        password_hash = User.hash_password(password)
        user = User(name=name, email=email, password_hash=password_hash)
        
        # Save to database
        user_dict = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'password_hash': user.password_hash,
            'created_at': user.created_at
        }
        self.users_collection.insert_one(user_dict)
        
        return user
    
    def authenticate_user(self, email, password):
        """Authenticate a user with email and password."""
        user_data = self.users_collection.find_one({'email': email})
        if not user_data:
            raise ValueError('Invalid email or password')
        
        # Verify password
        if not User.verify_password(password, user_data['password_hash']):
            raise ValueError('Invalid email or password')
        
        # Return user object
        return User.from_dict(user_data)
    
    def get_user_by_id(self, user_id):
        """Get user by ID."""
        user_data = self.users_collection.find_one({'id': user_id})
        if not user_data:
            return None
        return User.from_dict(user_data)
    
    def get_user_by_email(self, email):
        """Get user by email."""
        user_data = self.users_collection.find_one({'email': email})
        if not user_data:
            return None
        return User.from_dict(user_data)
