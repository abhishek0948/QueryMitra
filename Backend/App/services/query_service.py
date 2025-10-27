from flask import current_app
import json
import pandas as pd
import math  
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from .sql_to_mongo_service import SQLToMongoConverter

class QueryService:
    def __init__(self):
        self.db = current_app.db
        self.sql_converter = SQLToMongoConverter()
        
    def execute_query(self, dataset_id, query, mode):
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
                
            # Execute query on dataset collection
            collection_name = f'data_{dataset_id}'
            
            # Handle different query modes
            if mode == 'SQL':
                return self._execute_sql_query(collection_name, query)
            elif mode == 'Natural Language':
                return self._execute_nl_query(dataset_id, query)
            elif mode == 'MongoDB':
                return self._execute_aggregation_query(collection_name, query)
            else:
                # Fallback to aggregation for other modes
                return self._execute_aggregation_query(collection_name, query)
            
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
            import requests
            from flask import current_app
            import json
            
            # Get API key from config
            api_key = current_app.config.get('GEMINI_API_KEY')
            
            if not api_key:
                raise ValueError("Gemini API key is not configured")
            
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
            prompt = f"""
            You are an expert data analyst who translates natural language questions into executable MongoDB Aggregation Pipeline queries.
            Your response MUST be ONLY the JSON for the MongoDB aggregation pipeline, represented as a string. 
            Do not include any explanations, markdown formatting, or any text other than the JSON string itself.

            Dataset Schema:
            {json.dumps(schema, indent=2)}

            User Question:
            "{query}"

            Generate the MongoDB aggregation pipeline as a JSON string. For example:
            '[{{"$match":{{"gender":"female","employment_status":"employed"}}}},{{"$group":{{"_id":"$state","average_income":{{"$avg":"$monthly_income"}}}}}}]'
            """
            
            # Use direct REST API call instead of the Python library
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            
            response = requests.post(url, headers=headers, json=data)
            response_json = response.json()
            
            if "error" in response_json:
                error_message = response_json["error"].get("message", "Unknown error")
                raise ValueError(f"Gemini API error: {error_message}")
                
            # Extract generated text from response
            generated_text = ""
            if "candidates" in response_json:
                for candidate in response_json["candidates"]:
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "text" in part:
                                generated_text += part["text"]
            
            # Clean up the response (remove markdown code blocks if present)
            if generated_text.startswith('```json'):
                generated_text = generated_text.split('```json')[1]
            if generated_text.startswith('```'):
                generated_text = generated_text.split('```')[1]
            if generated_text.endswith('```'):
                generated_text = generated_text.rsplit('```', 1)[0]
                
            generated_text = generated_text.strip()
            
            # Validate the JSON
            try:
                mongo_query = json.loads(generated_text)
            except json.JSONDecodeError:
                # If the generated text is not valid JSON, use a simple query
                mongo_query = [{"$limit": 10}]
                
            # Execute the generated MongoDB query
            collection_name = f'data_{dataset_id}'
            result = self._execute_aggregation_query(collection_name, mongo_query)
            
            # Include the original NL query and generated MongoDB query in the result
            result['nl_query'] = query
            result['query'] = generated_text
            
            return result
            
        except Exception as e:
            # Log the error
            import traceback
            print(f"NL query error: {str(e)}")
            print(traceback.format_exc())
            
            # Return an error response
            return {
                'columns': ['error', 'message'],
                'rows': [{
                    'error': 'Natural language translation failed',
                    'message': f'{str(e)}. Try using SQL mode instead.'
                }],
                'query': query
            }