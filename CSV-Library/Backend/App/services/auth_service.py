from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from App.models.user import User


class AuthService:
    def __init__(self):
        self.db = current_app.db

    def register(self, name: str, email: str, password: str) -> dict:
        existing = self.db.users.find_one({'email': email})
        if existing:
            raise ValueError('An account with this email already exists')

        password_hash = generate_password_hash(password)
        user = User(name, email, password_hash)
        self.db.users.insert_one(user.to_dict())
        return user.to_public_dict()

    def login(self, email: str, password: str) -> dict:
        user_doc = self.db.users.find_one({'email': email})
        if not user_doc:
            raise ValueError('Invalid email or password')

        if not check_password_hash(user_doc['password_hash'], password):
            raise ValueError('Invalid email or password')

        return {
            'id': user_doc['id'],
            'name': user_doc['name'],
            'email': user_doc['email'],
        }

    def get_user_by_id(self, user_id: str) -> dict | None:
        user_doc = self.db.users.find_one({'id': user_id})
        if not user_doc:
            return None
        return {
            'id': user_doc['id'],
            'name': user_doc['name'],
            'email': user_doc['email'],
        }
