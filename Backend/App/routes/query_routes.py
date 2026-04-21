from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('queries', __name__, url_prefix='/api/queries')

@bp.route('/execute', methods=['POST'])
@jwt_required()
def execute_query():
    try:
        # Import and initialize the service inside the route function
        from App.services.query_service import QueryService
        query_service = QueryService()
        
        # Get current user ID from JWT token
        user_id = get_jwt_identity()
        
        data = request.json
        dataset_id = data.get('datasetId')
        query = data.get('query')
        mode = data.get('mode')
        
        if not all([dataset_id, query, mode]):
            return jsonify({'error': 'Missing required parameters'}), 400
            
        result = query_service.execute_query(dataset_id, query, mode, user_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500