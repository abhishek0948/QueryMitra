from flask import current_app
from App.models.user import User
from datetime import datetime

class AuthService:
    def __init__(self):
        self.db = current_app.db
        self.users_collection = self.db['users']
    
    def initialize_admin(self):
        """Initialize default admin user if not exists."""
        # Delete old admin user with just 'admin' as email
        self.users_collection.delete_one({'email': 'admin'})
        
        admin_email = 'admin@admin.com'
        existing_admin = self.users_collection.find_one({'email': admin_email})
        
        if not existing_admin:
            password_hash = User.hash_password('admin')
            admin_user = User(
                name='Admin',
                email=admin_email,
                password_hash=password_hash,
                role='admin'
            )
            admin_dict = {
                'id': admin_user.id,
                'name': admin_user.name,
                'email': admin_user.email,
                'password_hash': admin_user.password_hash,
                'role': admin_user.role,
                'created_at': admin_user.created_at
            }
            self.users_collection.insert_one(admin_dict)
            print("Admin user created successfully with email: admin@admin.com")
    
    def register_user(self, name, email, password, role='user'):
        """Register a new user."""
        # Check if user already exists
        existing_user = self.users_collection.find_one({'email': email})
        if existing_user:
            raise ValueError('User with this email already exists')
        
        # Create new user with hashed password
        password_hash = User.hash_password(password)
        user = User(name=name, email=email, password_hash=password_hash, role=role)
        
        # Save to database
        user_dict = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'password_hash': user.password_hash,
            'role': user.role,
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
    
    def get_all_users(self):
        """Get all users (admin only)."""
        users_data = self.users_collection.find()
        return [User.from_dict(user_data).to_dict() for user_data in users_data]
