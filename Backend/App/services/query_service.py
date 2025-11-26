from flask import current_app
import json
import pandas as pd
import math
import time
import requests
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from .sql_to_mongo_service import SQLToMongoConverter


class QueryService:
    def __init__(self):
        self.db = current_app.db
        self.sql_converter = SQLToMongoConverter()

    def execute_query(self, dataset_id, query, mode, user_id=None):
        start_time = time.time()
        
        try:
            # Get dataset metadata
            dataset = None
            if isinstance(self.db, dict):
                # Handle fallback dictionary case
                for ds in self.db.get("datasets", []):
                    if ds.get("id") == dataset_id:
                        dataset = ds
            else:
                # Normal MongoDB case
                dataset = self.db.datasets.find_one({'id': dataset_id})

            if not dataset:
                raise ValueError('Dataset not found')
            
            # Verify dataset ownership if user_id is provided
            if user_id and dataset.get('user_id') != user_id:
                raise ValueError('Access denied: You do not have permission to query this dataset')

            # Execute query on dataset collection
            collection_name = f'data_{dataset_id}'

            # Handle different query modes
            if mode == 'SQL':
                result = self._execute_sql_query(collection_name, query)
            elif mode == 'Natural Language':
                result = self._execute_nl_query(dataset_id, query)
            elif mode == 'MongoDB':
                result = self._execute_aggregation_query(collection_name, query)
            else:
                # Fallback to aggregation for other modes
                result = self._execute_aggregation_query(collection_name, query)
            
            # Calculate execution time
            execution_time = round((time.time() - start_time) * 1000, 2)  # Convert to milliseconds
            result['execution_time_ms'] = execution_time
            
            return result

        except json.JSONDecodeError:
            raise ValueError('Invalid query format. JSON expected.')
        except PyMongoError as e:
            raise Exception(f'Database error: {str(e)}')
        except Exception as e:
            raise Exception(f'Query execution failed: {str(e)}')

    def _execute_aggregation_query(self, collection_name, query):
        try:
            # Parse and execute MongoDB aggregation pipeline
            pipeline = json.loads(query) if isinstance(query, str) else query

            # Add default sort by _id to maintain original data order if no sort stage exists
            has_sort = any('$sort' in stage for stage in pipeline)
            if not has_sort:
                # Insert sort stage before any limit stage if it exists
                limit_index = None
                for i, stage in enumerate(pipeline):
                    if '$limit' in stage:
                        limit_index = i
                        break
                
                if limit_index is not None:
                    pipeline.insert(limit_index, {"$sort": {"_id": 1}})
                else:
                    pipeline.append({"$sort": {"_id": 1}})

            if isinstance(self.db, dict):
                # Handle fallback dictionary case - mock results
                mock_result = {
                    'columns': ['status', 'message'],
                    'rows': [{'status': 'success', 'message': 'Using fallback data store'}],
                    'query': str(query)
                }
                return mock_result

            collection = self.db[collection_name]
            cursor = collection.aggregate(pipeline)

            # Convert cursor to list and process results
            results = list(cursor)

            # Extract column names and rows
            if not results:
                return {'columns': [], 'rows': [], 'query': str(query)}

            columns = list(results[0].keys())

            # Handle NaN values by converting them to null (None in Python)
            rows = []
            for doc in results:
                row = {}
                for key, value in doc.items():
                    # Skip _id field
                    if key == '_id':
                        continue
                    # Convert NaN to None (null in JSON)
                    if isinstance(value, float) and math.isnan(value):
                        row[key] = None
                    else:
                        row[key] = value
                rows.append(row)

            return {
                'columns': columns,
                'rows': rows,
                'query': str(query)
            }
        except Exception as e:
            raise Exception(f'Aggregation query failed: {str(e)}')

    def _execute_sql_query(self, collection_name, query):
        """
        Execute SQL query by converting it to MongoDB aggregation pipeline
        """
        try:
            # Convert SQL to MongoDB aggregation pipeline
            pipeline = self.sql_converter.convert(query)

            if isinstance(self.db, dict):
                # Handle fallback dictionary case - mock results
                mock_result = {
                    'columns': ['status', 'message', 'converted_query'],
                    'rows': [{
                        'status': 'success',
                        'message': 'SQL converted to MongoDB pipeline (using fallback data store)',
                        'converted_query': str(pipeline)
                    }],
                    'query': query,
                    'converted_pipeline': pipeline
                }
                return mock_result

            # Execute the converted pipeline
            collection = self.db[collection_name]
            cursor = collection.aggregate(pipeline)

            # Convert cursor to list and process results
            results = list(cursor)

            # Extract column names and rows
            if not results:
                return {
                    'columns': [],
                    'rows': [],
                    'query': query,
                    'converted_pipeline': pipeline
                }

            columns = list(results[0].keys())

            # Handle NaN values and process results
            rows = []
            for doc in results:
                row = {}
                for key, value in doc.items():
                    # Skip _id field unless it's part of grouping
                    if key == '_id' and not isinstance(value, dict):
                        continue
                    # Convert NaN to None (null in JSON)
                    if isinstance(value, float) and math.isnan(value):
                        row[key] = None
                    else:
                        row[key] = value
                rows.append(row)

            return {
                'columns': [col for col in columns if col != '_id' or any(isinstance(row.get('_id'), dict) for row in results)],
                'rows': rows,
                'query': query,
                'converted_pipeline': pipeline
            }

        except ValueError as ve:
            # SQL parsing error
            return {
                'columns': ['error', 'message', 'suggestion'],
                'rows': [{
                    'error': 'SQL Parsing Error',
                    'message': str(ve),
                    'suggestion': 'Please check your SQL syntax. Supported: SELECT, WHERE, GROUP BY, ORDER BY, LIMIT'
                }],
                'query': query
            }
        except Exception as e:
            raise Exception(f'SQL query execution failed: {str(e)}')

    def _execute_nl_query(self, dataset_id, query):
        """
        Executes a natural language query by:
        1. Translating the NL query to a MongoDB aggregation pipeline using Google's Generative AI (Gemini)
        2. Executing the generated MongoDB query
        3. Returning the results
        """
        try:
            # Get API key from config
            api_key = current_app.config.get('GEMINI_API_KEY')

            if not api_key:
                raise ValueError(
                    "Gemini API key is not configured. Please set GEMINI_API_KEY in your environment variables.")

            # Get dataset schema for better query generation
            dataset = None
            if isinstance(self.db, dict):
                for ds in self.db.get("datasets", []):
                    if ds.get("id") == dataset_id:
                        dataset = ds
            else:
                dataset = self.db.datasets.find_one({'id': dataset_id})

            if not dataset or 'schema' not in dataset:
                raise ValueError('Dataset schema not found')

            schema = dataset.get('schema', {})

            # Prepare the prompt for Gemini
            prompt = """
You are an expert data analyst who translates natural language questions into executable MongoDB Aggregation Pipeline queries.
Your response MUST be ONLY the JSON for the MongoDB aggregation pipeline, represented as a valid JSON array string. 
Do not include any explanations, markdown formatting, code blocks, or any text other than the JSON array itself.

Dataset Schema (field names and types):
{schema}

Available sample field names from the dataset:
{fields}

User Question:
"{query}"

Rules:
1. Return ONLY a valid JSON array representing the MongoDB aggregation pipeline
2. Use exact field names from the schema provided
3. For aggregations, use appropriate MongoDB operators like $group, $match, $sort, $limit
4. For filtering, use $match stage
5. For calculations, use $group with aggregation operators like $avg, $sum, $count, $min, $max
6. Always include a reasonable $limit (like 100) unless specifically asked for all data
7. IMPORTANT: Unless explicitly asked to sort by a specific field, do NOT include $sort stage - the system will maintain original data order automatically
8. Only add $sort stage when the user explicitly asks for ordering (ascending, descending, sorted by, etc.)

Example format:
[{{"$match": {{"field_name": "value"}}}}, {{"$group": {{"_id": "$category", "average": {{"$avg": "$numeric_field"}}}}}}, {{"$limit": 100}}]
""".format(
                schema=json.dumps(schema, indent=2),
                fields=', '.join(schema.keys()),
                query=query
            )

            # Use direct REST API call to Gemini
            import requests
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 2048,
                }
            }

            print(f"Calling Gemini API for NL query: '{query}'")
            response = requests.post(
                url, headers=headers, json=data, timeout=30)

            if response.status_code != 200:
                raise ValueError(
                    f"Gemini API request failed with status {response.status_code}: {response.text}")

            response_json = response.json()

            if "error" in response_json:
                error_message = response_json["error"].get(
                    "message", "Unknown error")
                raise ValueError(f"Gemini API error: {error_message}")

            # Extract generated text from response
            generated_text = ""
            if "candidates" in response_json and len(response_json["candidates"]) > 0:
                candidate = response_json["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        if "text" in part:
                            generated_text += part["text"]

            if not generated_text:
                raise ValueError("No response generated from Gemini API")

            print(f"Gemini generated text: {generated_text}")

            # Clean up the response (remove markdown code blocks if present)
            cleaned_text = generated_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text.split('```json')[1]
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text.split('```')[1]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text.rsplit('```', 1)[0]

            cleaned_text = cleaned_text.strip()

            # Validate the JSON
            try:
                mongo_query = json.loads(cleaned_text)
                if not isinstance(mongo_query, list):
                    # If it's not a list, wrap it in a list
                    mongo_query = [mongo_query]
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Cleaned text: {cleaned_text}")
                # If the generated text is not valid JSON, create a simple fallback query
                if "limit" in query.lower() and any(word in query.lower() for word in ["all", "everything", "show", "display"]):
                    mongo_query = [{"$sort": {"_id": 1}}, {"$limit": 1000}]
                else:
                    mongo_query = [{"$sort": {"_id": 1}}, {"$limit": 100}]

            print(f"Final MongoDB query: {mongo_query}")

            # Execute the generated MongoDB query
            collection_name = f'data_{dataset_id}'
            result = self._execute_aggregation_query(
                collection_name, mongo_query)

            # Include the original NL query and generated MongoDB query in the result
            result['nl_query'] = query
            result['generated_mongo_query'] = mongo_query
            result['query'] = f"Natural Language: '{query}' -> MongoDB: {json.dumps(mongo_query)}"

            return result

        except Exception as e:
            # Log the error
            import traceback
            print(f"NL query error: {str(e)}")
            print(traceback.format_exc())

            # Return an error response with helpful information
            return {
                'columns': ['error', 'message', 'suggestion'],
                'rows': [{
                    'error': 'Natural language translation failed',
                    'message': str(e),
                    'suggestion': 'Try rephrasing your question or use SQL/MongoDB mode instead. Make sure to reference fields that exist in the dataset.'
                }],
                'query': query,
                'nl_query': query
            }
