from flask import current_app
import json
import pandas as pd
import math
import time
import requests
from pymongo.errors import PyMongoError
from .sql_to_mongo_service import SQLToMongoConverter
from .encryption_util import SimpleEncryptor


class QueryService:

    def __init__(self):
        self.db = current_app.db
        self.sql_converter = SQLToMongoConverter()
        self.encryptor = SimpleEncryptor()

    # ──────────────────────────────────────────────────────────────────────────
    # Public entry point
    # ──────────────────────────────────────────────────────────────────────────

    def execute_query(self, dataset_id, query, mode, user_id=None):
        start_time = time.time()

        try:
            # Get dataset metadata
            dataset = None
            if isinstance(self.db, dict):
                for ds in self.db.get("datasets", []):
                    if ds.get("id") == dataset_id:
                        dataset = ds
            else:
                dataset = self.db.datasets.find_one({'id': dataset_id})

            if not dataset:
                raise ValueError('Dataset not found')

            # Verify dataset ownership if user_id is provided
            if user_id and dataset.get('user_id') != user_id:
                raise ValueError('Access denied: You do not have permission to query this dataset')

            collection_name = f'data_{dataset_id}'

            if mode == 'SQL':
                result = self._execute_sql_query(collection_name, query)
            elif mode == 'Natural Language':
                result = self._execute_nl_query(dataset_id, query)
            elif mode == 'MongoDB':
                result = self._execute_aggregation_query(collection_name, query)
            else:
                result = self._execute_aggregation_query(collection_name, query)

            execution_time = round((time.time() - start_time) * 1000, 2)
            result['execution_time_ms'] = execution_time

            return self._convert_bytes(result)

        except json.JSONDecodeError:
            raise ValueError('Invalid query format. JSON expected.')
        except PyMongoError as e:
            raise Exception(f'Database error: {str(e)}')
        except Exception as e:
            raise Exception(f'Query execution failed: {str(e)}')

    # ──────────────────────────────────────────────────────────────────────────
    # Decrypt helper: fetch all documents and return as plain list of dicts
    # ──────────────────────────────────────────────────────────────────────────

    def _get_all_decrypted_records(self, collection_name):
        """
        Fetch every document from *collection_name* and return them as plain
        Python dicts.  Transparently handles the encrypted storage format where
        each MongoDB document is { "data": <Fernet ciphertext> }.
        """
        if isinstance(self.db, dict):
            return self.db.get(collection_name, [])

        raw_docs = list(self.db[collection_name].find({}, {'_id': 0}))
        if not raw_docs:
            return []

        # Detect encrypted format: every document has exactly one key "data"
        is_encrypted = all(list(doc.keys()) == ['data'] for doc in raw_docs)
        if not is_encrypted:
            return raw_docs  # legacy plain storage

        records = []
        for doc in raw_docs:
            try:
                decrypted = self.encryptor.decrypt(doc['data'])
                records.append(json.loads(decrypted.decode('utf-8')))
            except Exception as e:
                print(f'[QueryService] Decryption error on document: {e}')
        return records

    # ──────────────────────────────────────────────────────────────────────────
    # Result builder
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _records_to_result(records, query_str):
        if not records:
            return {'columns': [], 'rows': [], 'query': query_str}

        columns = list(records[0].keys())
        rows = []
        for rec in records:
            row = {}
            for k, v in rec.items():
                if isinstance(v, float) and math.isnan(v):
                    row[k] = None
                else:
                    row[k] = v
            rows.append(row)
        return {'columns': columns, 'rows': rows, 'query': query_str}

    # ──────────────────────────────────────────────────────────────────────────
    # MongoDB aggregation mode
    # Decrypt → DataFrame → apply pipeline stages in Python
    # ──────────────────────────────────────────────────────────────────────────

    def _execute_aggregation_query(self, collection_name, query):
        try:
            pipeline = json.loads(query) if isinstance(query, str) else query

            if isinstance(self.db, dict):
                return {
                    'columns': ['status', 'message'],
                    'rows': [{'status': 'success', 'message': 'Using fallback data store'}],
                    'query': str(query)
                }

            records = self._get_all_decrypted_records(collection_name)
            if not records:
                return {'columns': [], 'rows': [], 'query': str(query)}

            df = pd.DataFrame(records)
            df = self._apply_pipeline(df, pipeline)

            result_records = df.where(pd.notnull(df), None).to_dict('records')
            return self._records_to_result(result_records, str(query))

        except Exception as e:
            raise Exception(f'Aggregation query failed: {str(e)}')

    # ──────────────────────────────────────────────────────────────────────────
    # SQL mode
    # ──────────────────────────────────────────────────────────────────────────

    def _execute_sql_query(self, collection_name, query):
        """
        Convert SQL → MongoDB pipeline via sql_converter, then execute the
        pipeline in-memory on decrypted data.
        """
        try:
            pipeline = self.sql_converter.convert(query)

            if isinstance(self.db, dict):
                return {
                    'columns': ['status', 'message', 'converted_query'],
                    'rows': [{
                        'status': 'success',
                        'message': 'SQL converted to pipeline (using fallback data store)',
                        'converted_query': str(pipeline)
                    }],
                    'query': query,
                    'converted_pipeline': pipeline
                }

            records = self._get_all_decrypted_records(collection_name)
            if not records:
                return {'columns': [], 'rows': [], 'query': query, 'converted_pipeline': pipeline}

            df = pd.DataFrame(records)
            df = self._apply_pipeline(df, pipeline)

            result_records = df.where(pd.notnull(df), None).to_dict('records')
            result = self._records_to_result(result_records, query)
            result['converted_pipeline'] = pipeline
            return result

        except ValueError as ve:
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

    # ──────────────────────────────────────────────────────────────────────────
    # Natural Language mode
    # ──────────────────────────────────────────────────────────────────────────

    def _execute_nl_query(self, dataset_id, query):
        """
        Translate NL → MongoDB pipeline via Gemini, then execute the pipeline
        in-memory on decrypted data.
        """
        try:
            api_key = current_app.config.get('GEMINI_API_KEY')
            if not api_key:
                raise ValueError(
                    "Gemini API key is not configured. Please set GEMINI_API_KEY in your environment variables.")

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
3. For aggregations, use $group, $match, $sort, $limit
4. For filtering, use $match stage
5. For calculations, use $group with $avg, $sum, $count, $min, $max
6. Always include a reasonable $limit (like 100) unless specifically asked for all data
7. Unless explicitly asked to sort, do NOT include $sort

Example format:
[{{"$match": {{"field_name": "value"}}}}, {{"$limit": 100}}]
""".format(
                schema=json.dumps(schema, indent=2),
                fields=', '.join(schema.keys()),
                query=query
            )

            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash-lite:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 2048,
                }
            }

            print(f"Calling Gemini API for NL query: '{query}'")
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code != 200:
                raise ValueError(
                    f"Gemini API request failed with status {response.status_code}: {response.text}")

            response_json = response.json()

            if "error" in response_json:
                raise ValueError(f"Gemini API error: {response_json['error'].get('message', 'Unknown error')}")

            generated_text = ""
            candidates = response_json.get("candidates", [])
            if candidates:
                candidate = candidates[0]
                for part in candidate.get("content", {}).get("parts", []):
                    generated_text += part.get("text", "")

            if not generated_text:
                raise ValueError("No response generated from Gemini API")

            print(f"Gemini generated text: {generated_text}")

            cleaned = generated_text.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned.split('```json', 1)[1]
            if cleaned.startswith('```'):
                cleaned = cleaned.split('```', 1)[1]
            if cleaned.endswith('```'):
                cleaned = cleaned.rsplit('```', 1)[0]
            cleaned = cleaned.strip()

            try:
                mongo_query = json.loads(cleaned)
                if not isinstance(mongo_query, list):
                    mongo_query = [mongo_query]
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e} | text: {cleaned}")
                mongo_query = [{"$limit": 100}]

            print(f"Final MongoDB query: {mongo_query}")

            collection_name = f'data_{dataset_id}'
            result = self._execute_aggregation_query(collection_name, mongo_query)

            result['nl_query'] = query
            result['generated_mongo_query'] = mongo_query
            result['query'] = f"Natural Language: '{query}' -> MongoDB: {json.dumps(mongo_query)}"
            return result

        except Exception as e:
            import traceback
            print(f"NL query error: {str(e)}")
            print(traceback.format_exc())
            return {
                'columns': ['error', 'message', 'suggestion'],
                'rows': [{
                    'error': 'Natural language translation failed',
                    'message': str(e),
                    'suggestion': 'Try rephrasing your question or use SQL/MongoDB mode instead.'
                }],
                'query': query,
                'nl_query': query
            }

    # ──────────────────────────────────────────────────────────────────────────
    # In-memory pipeline executor (shared by all three modes)
    # ──────────────────────────────────────────────────────────────────────────

    def _apply_pipeline(self, df: pd.DataFrame, pipeline: list) -> pd.DataFrame:
        """Apply a list of MongoDB aggregation stages to a pandas DataFrame."""
        for stage in pipeline:
            if '$match' in stage:
                df = self._apply_match(df, stage['$match'])
            elif '$sort' in stage:
                sort_spec = stage['$sort']
                cols = list(sort_spec.keys())
                ascending = [v == 1 for v in sort_spec.values()]
                valid = [c for c in cols if c in df.columns]
                if valid:
                    df = df.sort_values(
                        by=valid,
                        ascending=[ascending[cols.index(c)] for c in valid]
                    )
            elif '$limit' in stage:
                df = df.head(int(stage['$limit']))
            elif '$skip' in stage:
                df = df.iloc[int(stage['$skip']):]
            elif '$project' in stage:
                proj = stage['$project']
                include = [k for k, v in proj.items() if v and k in df.columns]
                if include:
                    df = df[include]
            elif '$group' in stage:
                df = self._apply_group(df, stage['$group'])
            elif '$count' in stage:
                df = pd.DataFrame([{stage['$count']: len(df)}])
            elif '$unwind' in stage:
                field = stage['$unwind'].lstrip('$') if isinstance(stage['$unwind'], str) else stage['$unwind'].get('path', '').lstrip('$')
                if field in df.columns:
                    df = df.explode(field)
            # Unknown stages are silently skipped (best-effort)
        return df

    @staticmethod
    def _apply_match(df: pd.DataFrame, match_spec: dict) -> pd.DataFrame:
        """Apply a $match spec to a DataFrame."""
        mask = pd.Series([True] * len(df), index=df.index)
        for field, condition in match_spec.items():
            if field not in df.columns:
                continue
            if isinstance(condition, dict):
                for op, val in condition.items():
                    col = df[field]
                    num_col = pd.to_numeric(col, errors='coerce')
                    if op == '$eq':
                        mask &= col == val
                    elif op == '$ne':
                        mask &= col != val
                    elif op == '$gt':
                        mask &= num_col > val
                    elif op == '$gte':
                        mask &= num_col >= val
                    elif op == '$lt':
                        mask &= num_col < val
                    elif op == '$lte':
                        mask &= num_col <= val
                    elif op == '$in':
                        mask &= col.isin(val)
                    elif op == '$nin':
                        mask &= ~col.isin(val)
                    elif op == '$regex':
                        mask &= col.astype(str).str.contains(val, case=False, na=False, regex=True)
            else:
                mask &= df[field] == condition
        return df[mask]

    @staticmethod
    def _apply_group(df: pd.DataFrame, group_spec: dict) -> pd.DataFrame:
        """Apply a $group spec to a DataFrame."""
        group_id = group_spec.get('_id')
        agg_fields = {k: v for k, v in group_spec.items() if k != '_id'}

        def compute_agg(sub_df, out_field, expr):
            if not isinstance(expr, dict):
                return None
            op, src = list(expr.items())[0]
            col = src.lstrip('$') if isinstance(src, str) else None
            if op == '$sum' and src == 1:
                return len(sub_df)
            if col and col in df.columns:
                num = pd.to_numeric(sub_df[col], errors='coerce')
                if op == '$sum':
                    return num.sum()
                elif op == '$avg':
                    return num.mean()
                elif op == '$min':
                    return num.min()
                elif op == '$max':
                    return num.max()
                elif op == '$count':
                    return len(sub_df)
            return None

        if group_id is None:
            # Aggregate entire DataFrame
            row = {}
            for out_field, expr in agg_fields.items():
                row[out_field] = compute_agg(df, out_field, expr)
            return pd.DataFrame([row])

        group_col = group_id.lstrip('$') if isinstance(group_id, str) else None
        if group_col is None or group_col not in df.columns:
            return df

        result_rows = []
        for key, group_df in df.groupby(group_col, dropna=False):
            row = {'_id': key}
            for out_field, expr in agg_fields.items():
                row[out_field] = compute_agg(group_df, out_field, expr)
            result_rows.append(row)
        return pd.DataFrame(result_rows)

    # ──────────────────────────────────────────────────────────────────────────
    # Utility
    # ──────────────────────────────────────────────────────────────────────────

    def _convert_bytes(self, obj):
        """Recursively convert bytes objects in dicts/lists to strings."""
        if isinstance(obj, dict):
            return {k: self._convert_bytes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_bytes(i) for i in obj]
        elif isinstance(obj, bytes):
            try:
                return obj.decode('utf-8')
            except Exception:
                return str(obj)
        else:
            return obj
