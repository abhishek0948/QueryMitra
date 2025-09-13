import pandas as pd
import os
import json
from flask import current_app
from App.models.dataset import Dataset

class DatasetService:
    def __init__(self):
        self.db = current_app.db
        
    def get_all_datasets(self):
        try:
            if isinstance(self.db, dict):
                # Handle fallback dictionary case
                return self.db.get("datasets", [])
            else:
                # Normal MongoDB case
                datasets = list(self.db.datasets.find({}, {'_id': 0}))
                return datasets
        except Exception as e:
            print(f"Error getting datasets: {str(e)}")
            return []
        
    def create_dataset(self, file_path, name, description):
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            # Read CSV and infer schema
            df = pd.read_csv(file_path)
            schema = self._infer_schema(df)
            
            # Create dataset metadata
            dataset = Dataset(name, description, file_path, schema)
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