from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password', '')

        if not name or not email or not password:
            return jsonify({'error': 'Name, email and password are required'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        from App.services.auth_service import AuthService
        auth_service = AuthService()
        user = auth_service.register(name, email, password)

        token = create_access_token(identity=user['id'])
        return jsonify({'user': user, 'access_token': token}), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        from App.services.auth_service import AuthService
        auth_service = AuthService()
        user = auth_service.login(email, password)

        token = create_access_token(identity=user['id'])
        return jsonify({'user': user, 'access_token': token}), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/verify', methods=['GET'])
@jwt_required()
def verify():
    try:
        user_id = get_jwt_identity()
        from App.services.auth_service import AuthService
        auth_service = AuthService()
        user = auth_service.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'user': user}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
