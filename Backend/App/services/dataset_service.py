import pandas as pd
import os
import json
from flask import current_app
from App.models.dataset import Dataset

class DatasetService:
    def __init__(self):
        self.db = current_app.db
        
    def get_all_datasets(self, user_id=None):
        try:
            if isinstance(self.db, dict):
                # Handle fallback dictionary case
                all_datasets = self.db.get("datasets", [])
                if user_id:
                    return [d for d in all_datasets if d.get('user_id') == user_id]
                return all_datasets
            else:
                # Normal MongoDB case
                query = {'user_id': user_id} if user_id else {}
                datasets = list(self.db.datasets.find(query, {'_id': 0}))
                return datasets
        except Exception as e:
            print(f"Error getting datasets: {str(e)}")
            return []
        
    def create_dataset(self, file_path, name, description, user_id=None):
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            # Read CSV and infer schema
            df = pd.read_csv(file_path)
            schema = self._infer_schema(df)
            
            # Create dataset metadata with user_id
            dataset = Dataset(name, description, file_path, schema, user_id)
            dataset_dict = dataset.to_dict()
            
            # Save dataset metadata
            if isinstance(self.db, dict):
                # Handle fallback dictionary case
                if "datasets" not in self.db:
                    self.db["datasets"] = []
                self.db["datasets"].append(dataset_dict)
                
                # Save data to a JSON file as fallback
                fallback_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'fallback_data')
                os.makedirs(fallback_dir, exist_ok=True)
                
                records = df.to_dict('records')
                with open(os.path.join(fallback_dir, f'data_{dataset.id}.json'), 'w') as f:
                    json.dump(records, f)
            else:
                # Normal MongoDB case
                self.db.datasets.insert_one(dataset_dict)
                
                # Save dataset contents
                collection_name = f'data_{dataset.id}'
                records = df.to_dict('records')
                if records:
                    self.db[collection_name].insert_many(records)
            
            return dataset
        except pd.errors.EmptyDataError:
            raise ValueError("The CSV file is empty")
        except pd.errors.ParserError:
            raise ValueError("Error parsing CSV file - check the format")
        except Exception as e:
            raise Exception(f"Failed to create dataset: {str(e)}")
        
    def delete_dataset(self, dataset_id, user_id):
        try:
            if isinstance(self.db, dict):
                # Handle fallback dictionary case
                datasets = self.db.get("datasets", [])
                dataset = next((d for d in datasets if d.get('id') == dataset_id), None)
                
                if not dataset:
                    return False
                    
                # Verify ownership
                if dataset.get('user_id') != user_id:
                    return False
                    
                # Remove from list
                self.db["datasets"] = [d for d in datasets if d.get('id') != dataset_id]
                
                # Delete fallback data file
                fallback_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'fallback_data')
                data_file = os.path.join(fallback_dir, f'data_{dataset_id}.json')
                if os.path.exists(data_file):
                    os.remove(data_file)
                    
                # Delete uploaded file if it exists
                if dataset.get('file_path') and os.path.exists(dataset['file_path']):
                    os.remove(dataset['file_path'])
                    
                return True
            else:
                # Normal MongoDB case
                dataset = self.db.datasets.find_one({'id': dataset_id})
                
                if not dataset:
                    return False
                    
                # Verify ownership
                if dataset.get('user_id') != user_id:
                    return False
                    
                # Delete dataset metadata
                self.db.datasets.delete_one({'id': dataset_id})
                
                # Delete dataset contents collection
                collection_name = f'data_{dataset_id}'
                self.db[collection_name].drop()
                
                # Delete uploaded file if it exists
                if dataset.get('file_path') and os.path.exists(dataset['file_path']):
                    os.remove(dataset['file_path'])
                    
                return True
        except Exception as e:
            print(f"Error deleting dataset: {str(e)}")
            return False
    
    def _infer_schema(self, df):
        schema = {}
        for column in df.columns:
            if pd.api.types.is_numeric_dtype(df[column]):
                schema[column] = 'number'
            elif pd.api.types.is_bool_dtype(df[column]):
                schema[column] = 'boolean'
            else:
                schema[column] = 'string'
        return schema