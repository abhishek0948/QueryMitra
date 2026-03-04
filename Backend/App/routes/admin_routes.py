from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from App.services.auth_service import AuthService
from functools import wraps
import os

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def admin_required():
    """Decorator to require admin role for route access."""
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

@bp.route('/users', methods=['GET'])
@admin_required()
def get_all_users():
    """Get all users with their uploaded datasets (Admin only)."""
    try:
        auth_service = AuthService()
        
        # Get all users
        users = auth_service.get_all_users()
        
        # Get datasets collection
        datasets_collection = current_app.db['datasets']
        
        # Enrich users with their datasets
        for user in users:
            user_datasets = list(datasets_collection.find({'user_id': user['id']}))
            
            # Remove MongoDB _id field and format datasets
            for dataset in user_datasets:
                if '_id' in dataset:
                    del dataset['_id']
                if 'created_at' in dataset:
                    dataset['created_at'] = dataset['created_at'].isoformat() if hasattr(dataset['created_at'], 'isoformat') else str(dataset['created_at'])
            
            user['datasets'] = user_datasets
            user['dataset_count'] = len(user_datasets)
        
        return jsonify({
            'users': users,
            'total_users': len(users)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/datasets', methods=['GET'])
@admin_required()
def get_all_datasets():
    """Get all datasets from all users (Admin only)."""
    try:
        datasets_collection = current_app.db['datasets']
        users_collection = current_app.db['users']
        
        # Get all datasets
        all_datasets = list(datasets_collection.find())
        
        # Enrich datasets with user information
        for dataset in all_datasets:
            if '_id' in dataset:
                del dataset['_id']
            
            # Ensure filename is included
            if 'filename' not in dataset:
                dataset['filename'] = 'dataset.csv'
            
            # Get user information
            if 'user_id' in dataset:
                user = users_collection.find_one({'id': dataset['user_id']})
                if user:
                    dataset['user_name'] = user.get('name', 'Unknown')
                    dataset['user_email'] = user.get('email', 'Unknown')
                else:
                    dataset['user_name'] = 'Unknown'
                    dataset['user_email'] = 'Unknown'
                    dataset['user_email'] = 'Unknown'
            
            # Format created_at
            if 'created_at' in dataset:
                dataset['created_at'] = dataset['created_at'].isoformat() if hasattr(dataset['created_at'], 'isoformat') else str(dataset['created_at'])
        
        return jsonify({
            'datasets': all_datasets,
            'total_datasets': len(all_datasets)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/stats', methods=['GET'])
@admin_required()
def get_admin_stats():
    """Get overall statistics (Admin only)."""
    try:
        users_collection = current_app.db['users']
        datasets_collection = current_app.db['datasets']
        
        # Count users by role
        total_users = users_collection.count_documents({})
        admin_users = users_collection.count_documents({'role': 'admin'})
        regular_users = users_collection.count_documents({'role': 'user'})
        
        # Count datasets
        total_datasets = datasets_collection.count_documents({})
        
        # Get recent users (last 10)
        recent_users = list(users_collection.find().sort('created_at', -1).limit(10))
        for user in recent_users:
            if '_id' in user:
                del user['_id']
            if 'password_hash' in user:
                del user['password_hash']
            if 'created_at' in user:
                user['created_at'] = user['created_at'].isoformat() if hasattr(user['created_at'], 'isoformat') else str(user['created_at'])
        
        return jsonify({
            'total_users': total_users,
            'admin_users': admin_users,
            'regular_users': regular_users,
            'total_datasets': total_datasets,
            'recent_users': recent_users
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/datasets/<dataset_id>/download', methods=['GET'])
@admin_required()
def download_dataset(dataset_id):
    """Download a dataset file (Admin only)."""
    try:
        datasets_collection = current_app.db['datasets']
        
        # Get dataset information
        dataset = datasets_collection.find_one({'id': dataset_id})
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Get the filename (strip directory prefix if stored as full/relative path)
        filename = dataset.get('filename')
        if not filename:
            return jsonify({'error': 'Dataset filename not found in database'}), 404
        
        base_filename = os.path.basename(filename)
        
        # Always resolve to absolute path
        upload_folder = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
        file_path = os.path.join(upload_folder, base_filename)
        
        print(f"Stored filename: {filename}")        # Debug log
        print(f"Upload folder (abs): {upload_folder}") # Debug log
        print(f"Resolved file path: {file_path}")      # Debug log
        
        if not os.path.exists(file_path):
            return jsonify({'error': f'Dataset file not found at: {file_path}'}), 404
        
        # Send the file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=base_filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        print(f"Error downloading dataset: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

@bp.route('/datasets/<dataset_id>/preview', methods=['GET'])
@admin_required()
def preview_dataset(dataset_id):
    """Preview dataset content (Admin only)."""
    try:
        datasets_collection = current_app.db['datasets']
        
        # Get dataset information
        dataset = datasets_collection.find_one({'id': dataset_id})
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Get the file path (strip directory prefix if stored as full/relative path)
        raw_filename = dataset.get('filename', '')
        base_filename = os.path.basename(raw_filename)
        
        # Always resolve to absolute path
        upload_folder = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
        file_path = os.path.join(upload_folder, base_filename)
        
        print(f"Resolved preview path: {file_path}")  # Debug log
        
        if not os.path.exists(file_path):
            return jsonify({'error': f'Dataset file not found at: {file_path}'}), 404
        
        # Read first 100 rows for preview
        import pandas as pd
        df = pd.read_csv(file_path, nrows=100)
        
        preview_data = {
            'columns': df.columns.tolist(),
            'rows': df.head(20).to_dict('records'),  # First 20 rows
            'total_rows_in_file': len(df),
            'total_columns': len(df.columns)
        }
        
        return jsonify(preview_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
