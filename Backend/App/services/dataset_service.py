import pandas as pd
import os
import json
import pdfplumber
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
        
    def _read_file_as_dataframe(self, file_path):
        """Read a CSV or PDF file and return a pandas DataFrame."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.csv':
            return pd.read_csv(file_path)

        elif ext == '.pdf':
            return self._extract_tables_from_pdf(file_path)

        else:
            raise ValueError(f"Unsupported file format '{ext}'. Please upload a CSV or PDF file.")

    def _extract_tables_from_pdf(self, file_path):
        """Extract all tables from a PDF and merge them into a single DataFrame."""
        all_frames = []

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue
                    # First row is treated as header
                    headers = [str(h).strip() if h is not None else f'col_{i}'
                               for i, h in enumerate(table[0])]
                    rows = []
                    for row in table[1:]:
                        cleaned = [str(cell).strip() if cell is not None else ''
                                   for cell in row]
                        rows.append(cleaned)
                    if rows:
                        df = pd.DataFrame(rows, columns=headers)
                        all_frames.append(df)

        if not all_frames:
            raise ValueError(
                "No tables were found in the PDF. "
                "Please make sure the PDF contains structured table data."
            )

        # Concatenate all tables; reset index so rows are numbered sequentially
        merged = pd.concat(all_frames, ignore_index=True)

        # Attempt numeric coercion for columns that look numeric
        for col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors='ignore')

        return merged

    def create_dataset(self, file_path, name, description, user_id=None):
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Read file (CSV or PDF) and infer schema
            df = self._read_file_as_dataframe(file_path)
            schema = self._infer_schema(df)

            # Extract just the base filename (not full path)
            base_filename = os.path.basename(file_path)

            # Create dataset metadata with user_id
            dataset = Dataset(name, description, base_filename, schema, user_id)
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