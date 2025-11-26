from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os

bp = Blueprint('datasets', __name__, url_prefix='/api/datasets')

@bp.route('/', methods=['GET'])
@jwt_required()
def get_datasets():
    try:
        # Import and initialize the service inside the route function
        from App.services.dataset_service import DatasetService
        dataset_service = DatasetService()
        
        # Get current user ID from JWT token
        user_id = get_jwt_identity()
        
        datasets = dataset_service.get_all_datasets(user_id)
        return jsonify(datasets), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/', methods=['POST'])
@jwt_required()
def upload_dataset():
    try:
        # Import and initialize the service inside the route function
        from App.services.dataset_service import DatasetService
        dataset_service = DatasetService()
        
        # Get current user ID from JWT token
        user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not name or not description:
            return jsonify({'error': 'Name and description are required'}), 400
            
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        dataset = dataset_service.create_dataset(file_path, name, description, user_id)
        return jsonify(dataset.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500