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
    """Download a dataset as CSV reconstructed from MongoDB (Admin only)."""
    try:
        import io
        import csv
        from flask import Response
        from App.services.dataset_service import DatasetService

        dataset_service = DatasetService()

        # Load records from MongoDB (decrypted)
        records = dataset_service.load_dataset_records(dataset_id)
        if not records:
            return jsonify({'error': 'Dataset not found or has no data'}), 404

        # Build CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
        output.seek(0)

        filename = f"dataset_{dataset_id}.csv"
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )

    except Exception as e:
        print(f"Error downloading dataset: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/datasets/<dataset_id>/preview', methods=['GET'])
@admin_required()
def preview_dataset(dataset_id):
    """Preview dataset content from MongoDB (Admin only)."""
    try:
        from App.services.dataset_service import DatasetService

        dataset_service = DatasetService()

        # Load records from MongoDB (decrypted)
        records = dataset_service.load_dataset_records(dataset_id)
        if not records:
            return jsonify({'error': 'Dataset not found or has no data'}), 404

        columns = list(records[0].keys()) if records else []
        preview_data = {
            'columns': columns,
            'rows': records[:20],          # First 20 rows
            'total_rows_in_file': len(records),
            'total_columns': len(columns)
        }

        return jsonify(preview_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

