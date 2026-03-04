from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from App.services.auth_service import AuthService
from App.services.email_service import EmailService
from App.models.user import User
from App.models.pending_user import PendingUser

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/signup', methods=['POST'])
def signup():
    """Register a new user - sends OTP for email verification."""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not all(k in data for k in ('name', 'email', 'password')):
            return jsonify({'error': 'Name, email, and password are required'}), 400
        
        name = data['name']
        email = data['email']
        password = data['password']
        
        # Basic validation
        if not name or len(name) < 2:
            return jsonify({'error': 'Name must be at least 2 characters'}), 400
        
        if not email or '@' not in email:
            return jsonify({'error': 'Valid email is required'}), 400
        
        if not password or len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        auth_service = AuthService()
        
        # Check if user already exists
        existing_user = auth_service.get_user_by_email(email)
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Hash password and create pending user
        password_hash = User.hash_password(password)
        pending_user = PendingUser(name=name, email=email, password_hash=password_hash)
        
        # Store pending user temporarily
        current_app.db['pending_users'].delete_many({'email': email})  # Delete any existing pending user
        current_app.db['pending_users'].insert_one(pending_user.to_dict())
        
        # Generate and send OTP
        email_service = EmailService()
        otp = email_service.generate_otp()
        email_service.store_otp(email, otp)
        
        success, message = email_service.send_otp_email(email, otp)
        
        if not success:
            return jsonify({'error': message}), 500
        
        return jsonify({
            'message': 'OTP sent to your email. Please verify to complete registration.',
            'email': email
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and complete user registration."""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('email', 'otp')):
            return jsonify({'error': 'Email and OTP are required'}), 400
        
        email = data['email']
        otp = data['otp']
        
        # Verify OTP
        email_service = EmailService()
        is_valid, message = email_service.verify_otp(email, otp)
        
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Get pending user
        pending_user_data = current_app.db['pending_users'].find_one({'email': email})
        if not pending_user_data:
            return jsonify({'error': 'No pending registration found for this email'}), 404
        
        # Create actual user
        auth_service = AuthService()
        user = User(
            name=pending_user_data['name'],
            email=pending_user_data['email'],
            password_hash=pending_user_data['password_hash']
        )
        
        user_dict = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'password_hash': user.password_hash,
            'role': user.role,
            'created_at': user.created_at
        }
        current_app.db['users'].insert_one(user_dict)
        
        # Delete pending user
        current_app.db['pending_users'].delete_one({'email': email})
        
        # Create access token with additional claims
        access_token = create_access_token(
            identity=user.id,
            additional_claims={'role': user.role}
        )
        
        return jsonify({
            'message': 'Email verified successfully',
            'user': user.to_dict(),
            'access_token': access_token
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP to user's email."""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400
        
        email = data['email']
        
        # Check if pending user exists
        pending_user = current_app.db['pending_users'].find_one({'email': email})
        if not pending_user:
            return jsonify({'error': 'No pending registration found for this email'}), 404
        
        # Generate and send new OTP
        email_service = EmailService()
        otp = email_service.generate_otp()
        email_service.store_otp(email, otp)
        
        success, message = email_service.send_otp_email(email, otp)
        
        if not success:
            return jsonify({'error': message}), 500
        
        return jsonify({'message': 'New OTP sent to your email'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/login', methods=['POST'])
def login():
    """Authenticate a user and return a token."""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not all(k in data for k in ('email', 'password')):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email']
        password = data['password']
        
        # Authenticate user
        auth_service = AuthService()
        user = auth_service.authenticate_user(email, password)
        
        # Create access token with additional claims
        access_token = create_access_token(
            identity=user.id,
            additional_claims={'role': user.role}
        )
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current logged-in user information."""
    try:
        user_id = get_jwt_identity()
        auth_service = AuthService()
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """Verify if the token is valid."""
    try:
        user_id = get_jwt_identity()
        return jsonify({'valid': True, 'user_id': user_id}), 200
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 401
