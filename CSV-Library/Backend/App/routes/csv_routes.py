import os
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

bp = Blueprint('csvs', __name__, url_prefix='/api/csvs')

ALLOWED_EXTENSIONS = {'csv'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/', methods=['GET'])
@jwt_required()
def list_csvs():
    """Return all shared CSV files (every authenticated user can see them)."""
    try:
        from App.services.csv_service import CSVService
        csv_service = CSVService()
        return jsonify(csv_service.get_all()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/', methods=['POST'])
@jwt_required()
def upload_csv():
    """Upload a CSV. It immediately becomes visible to all users."""
    try:
        user_id = get_jwt_identity()

        from App.services.auth_service import AuthService
        auth_service = AuthService()
        user = auth_service.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        name = (request.form.get('name') or '').strip()
        description = (request.form.get('description') or '').strip()

        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only CSV files are allowed'}), 400
        if not name or not description:
            return jsonify({'error': 'Name and description are required'}), 400

        # Use a unique filename to avoid collisions
        base_name = secure_filename(file.filename)
        stem, ext = os.path.splitext(base_name)
        unique_name = f"{stem}_{uuid.uuid4().hex[:8]}{ext}"

        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
        file.save(file_path)

        from App.services.csv_service import CSVService
        csv_service = CSVService()
        doc = csv_service.create(file_path, name, description, user_id, user['name'])
        return jsonify(doc), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<csv_id>/preview', methods=['GET'])
@jwt_required()
def preview_csv(csv_id: str):
    """Return the first 20 rows of the CSV."""
    try:
        from App.services.csv_service import CSVService
        csv_service = CSVService()
        preview = csv_service.preview(csv_id)
        if preview is None:
            return jsonify({'error': 'CSV not found or file is missing'}), 404
        return jsonify(preview), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<csv_id>/download', methods=['GET'])
@jwt_required()
def download_csv(csv_id: str):
    """Download the original CSV file."""
    try:
        from App.services.csv_service import CSVService
        csv_service = CSVService()
        file_path, filename = csv_service.get_file_path(csv_id)

        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        return send_file(
            file_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<csv_id>', methods=['DELETE'])
@jwt_required()
def delete_csv(csv_id: str):
    """Delete a CSV. Only the uploader can delete their own file."""
    try:
        user_id = get_jwt_identity()
        from App.services.csv_service import CSVService
        csv_service = CSVService()
        success, message = csv_service.delete(csv_id, user_id)

        if not success:
            status_code = 403 if 'Unauthorized' in message else 404
            return jsonify({'error': message}), status_code

        return jsonify({'message': message}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
