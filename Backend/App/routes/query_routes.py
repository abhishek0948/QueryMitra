from flask import Blueprint, request, jsonify

bp = Blueprint('queries', __name__, url_prefix='/api/queries')

@bp.route('/execute', methods=['POST'])
def execute_query():
    try:
        # Import and initialize the service inside the route function
        from App.services.query_service import QueryService
        query_service = QueryService()
        
        data = request.json
        dataset_id = data.get('datasetId')
        query = data.get('query')
        mode = data.get('mode')
        
        if not all([dataset_id, query, mode]):
            return jsonify({'error': 'Missing required parameters'}), 400
            
        result = query_service.execute_query(dataset_id, query, mode)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500