from typing import Dict, List, Any, Union
import re

class SQLToMongoConverter:
    """
    Convert SQL queries to MongoDB aggregation pipelines.
    Supports SELECT, WHERE, GROUP BY, ORDER BY, LIMIT, HAVING operations.
    """
    
    def __init__(self):
        self.operators_map = {
            '=': '$eq',
            '!=': '$ne',
            '<>': '$ne',
            '>': '$gt',
            '>=': '$gte',
            '<': '$lt',
            '<=': '$lte',
            'LIKE': '$regex',
            'IN': '$in',
            'NOT IN': '$nin'
        }
    
    def convert(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Main conversion method that returns MongoDB aggregation pipeline
        """
        try:
            sql_query = self._clean_sql(sql_query)
            parsed = self._parse_sql(sql_query)
            pipeline = self._build_pipeline(parsed)
            return pipeline
        except Exception as e:
            raise ValueError(f"SQL parsing error: {str(e)}")
    
    def _clean_sql(self, sql: str) -> str:
        """Clean and normalize SQL query"""
        # Remove extra whitespace and normalize
        sql = re.sub(r'\s+', ' ', sql.strip())
        # Remove semicolon at the end
        sql = sql.rstrip(';')
        return sql
    
    def _parse_sql(self, sql: str) -> Dict[str, Any]:
        """Parse SQL query into components"""
        sql_upper = sql.upper()
        
        # Extract main clauses
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_upper)
        from_match = re.search(r'FROM\s+(\w+)', sql_upper)
        where_match = re.search(r'WHERE\s+(.*?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s+LIMIT|$)', sql_upper)
        group_by_match = re.search(r'GROUP\s+BY\s+(.*?)(?:\s+HAVING|\s+ORDER\s+BY|\s+LIMIT|$)', sql_upper)
        having_match = re.search(r'HAVING\s+(.*?)(?:\s+ORDER\s+BY|\s+LIMIT|$)', sql_upper)
        order_by_match = re.search(r'ORDER\s+BY\s+(.*?)(?:\s+LIMIT|$)', sql_upper)
        limit_match = re.search(r'LIMIT\s+(\d+)', sql_upper)
        
        # Get original case for field names
        select_original = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE)
        where_original = re.search(r'WHERE\s+(.*?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s+LIMIT|$)', sql, re.IGNORECASE)
        group_by_original = re.search(r'GROUP\s+BY\s+(.*?)(?:\s+HAVING|\s+ORDER\s+BY|\s+LIMIT|$)', sql, re.IGNORECASE)
        having_original = re.search(r'HAVING\s+(.*?)(?:\s+ORDER\s+BY|\s+LIMIT|$)', sql, re.IGNORECASE)
        order_by_original = re.search(r'ORDER\s+BY\s+(.*?)(?:\s+LIMIT|$)', sql, re.IGNORECASE)
        
        return {
            'select': select_original.group(1) if select_original else '*',
            'from': from_match.group(1) if from_match else None,
            'where': where_original.group(1) if where_original else None,
            'group_by': group_by_original.group(1) if group_by_original else None,
            'having': having_original.group(1) if having_original else None,
            'order_by': order_by_original.group(1) if order_by_original else None,
            'limit': int(limit_match.group(1)) if limit_match else None
        }
    
    def _build_pipeline(self, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build MongoDB aggregation pipeline from parsed SQL"""
        pipeline = []
        
        # 1. Handle WHERE clause (match stage)
        if parsed['where']:
            match_condition = self._parse_where_clause(parsed['where'])
            if match_condition:
                pipeline.append({"$match": match_condition})
        
        # 2. Handle GROUP BY clause
        if parsed['group_by']:
            group_stage = self._parse_group_by(parsed['select'], parsed['group_by'])
            pipeline.append(group_stage)
        else:
            # Handle SELECT without GROUP BY
            projection = self._parse_select_clause(parsed['select'])
            if projection and projection != {'*': 1}:
                pipeline.append({"$project": projection})
        
        # 3. Handle HAVING clause
        if parsed['having']:
            having_condition = self._parse_where_clause(parsed['having'])
            if having_condition:
                pipeline.append({"$match": having_condition})
        
        # 4. Handle ORDER BY clause
        if parsed['order_by']:
            sort_stage = self._parse_order_by(parsed['order_by'])
            if sort_stage:
                pipeline.append({"$sort": sort_stage})
        
        # 5. Handle LIMIT clause
        if parsed['limit']:
            pipeline.append({"$limit": parsed['limit']})
        
        # If no pipeline stages, return a simple find all with limit
        if not pipeline:
            pipeline.append({"$limit": 100})  # Default limit
        
        return pipeline
    
    def _parse_select_clause(self, select_clause: str) -> Dict[str, Any]:
        """Parse SELECT clause"""
        if select_clause.strip() == '*':
            return {}
        
        projection = {}
        fields = [f.strip() for f in select_clause.split(',')]
        
        for field in fields:
            # Handle aggregate functions
            if self._is_aggregate_function(field):
                continue  # Aggregates are handled in GROUP BY
            else:
                # Regular field
                field_name = field.strip()
                projection[field_name] = 1
        
        return projection
    
    def _parse_where_clause(self, where_clause: str) -> Dict[str, Any]:
        """Parse WHERE clause into MongoDB match conditions"""
        if not where_clause:
            return {}
        
        # Handle AND/OR logic
        if ' AND ' in where_clause.upper():
            conditions = re.split(r'\s+AND\s+', where_clause, flags=re.IGNORECASE)
            return {"$and": [self._parse_single_condition(cond) for cond in conditions]}
        elif ' OR ' in where_clause.upper():
            conditions = re.split(r'\s+OR\s+', where_clause, flags=re.IGNORECASE)
            return {"$or": [self._parse_single_condition(cond) for cond in conditions]}
        else:
            return self._parse_single_condition(where_clause)
    
    def _parse_single_condition(self, condition: str) -> Dict[str, Any]:
        """Parse a single WHERE condition"""
        condition = condition.strip()
        
        # Handle LIKE operator
        like_match = re.search(r'(\w+)\s+LIKE\s+[\'"](.+?)[\'"]', condition, re.IGNORECASE)
        if like_match:
            field, pattern = like_match.groups()
            # Convert SQL LIKE pattern to regex
            regex_pattern = pattern.replace('%', '.*').replace('_', '.')
            return {field: {"$regex": regex_pattern, "$options": "i"}}
        
        # Handle IN operator
        in_match = re.search(r'(\w+)\s+IN\s+\((.+?)\)', condition, re.IGNORECASE)
        if in_match:
            field, values = in_match.groups()
            value_list = [v.strip().strip('\'"') for v in values.split(',')]
            # Convert to appropriate types
            converted_values = []
            for v in value_list:
                if v.isdigit():
                    converted_values.append(int(v))
                elif self._is_float(v):
                    converted_values.append(float(v))
                else:
                    converted_values.append(v)
            return {field: {"$in": converted_values}}
        
        # Handle NOT IN operator
        not_in_match = re.search(r'(\w+)\s+NOT\s+IN\s+\((.+?)\)', condition, re.IGNORECASE)
        if not_in_match:
            field, values = not_in_match.groups()
            value_list = [v.strip().strip('\'"') for v in values.split(',')]
            # Convert to appropriate types
            converted_values = []
            for v in value_list:
                if v.isdigit():
                    converted_values.append(int(v))
                elif self._is_float(v):
                    converted_values.append(float(v))
                else:
                    converted_values.append(v)
            return {field: {"$nin": converted_values}}
        
        # Handle comparison operators
        for op in ['>=', '<=', '!=', '<>', '>', '<', '=']:
            if f' {op} ' in condition:
                parts = condition.split(f' {op} ')
                if len(parts) == 2:
                    field = parts[0].strip()
                    value = parts[1].strip().strip('\'"')
                    
                    # Convert value to appropriate type
                    if value.isdigit():
                        value = int(value)
                    elif self._is_float(value):
                        value = float(value)
                    
                    mongo_op = self.operators_map.get(op, '$eq')
                    if mongo_op == '$eq':
                        return {field: value}
                    else:
                        return {field: {mongo_op: value}}
        
        return {}
    
    def _parse_group_by(self, select_clause: str, group_by_clause: str) -> Dict[str, Any]:
        """Parse GROUP BY clause"""
        group_fields = [f.strip() for f in group_by_clause.split(',')]
        
        # Build _id for grouping
        if len(group_fields) == 1:
            group_id = f"${group_fields[0]}"
        else:
            group_id = {field: f"${field}" for field in group_fields}
        
        group_stage = {
            "$group": {
                "_id": group_id
            }
        }
        
        # Parse SELECT for aggregate functions
        select_fields = [f.strip() for f in select_clause.split(',')]
        for field in select_fields:
            if self._is_aggregate_function(field):
                agg_func, agg_field = self._parse_aggregate_function(field)
                if agg_func and agg_field:
                    group_stage["$group"][field] = {f"${agg_func}": f"${agg_field}"}
        
        return group_stage
    
    def _parse_order_by(self, order_by_clause: str) -> Dict[str, int]:
        """Parse ORDER BY clause"""
        sort_spec = {}
        fields = [f.strip() for f in order_by_clause.split(',')]
        
        for field in fields:
            if ' DESC' in field.upper():
                field_name = field.replace(' DESC', '').replace(' desc', '').strip()
                sort_spec[field_name] = -1
            elif ' ASC' in field.upper():
                field_name = field.replace(' ASC', '').replace(' asc', '').strip()
                sort_spec[field_name] = 1
            else:
                sort_spec[field.strip()] = 1
        
        return sort_spec
    
    def _is_aggregate_function(self, field: str) -> bool:
        """Check if field contains aggregate function"""
        agg_functions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']
        field_upper = field.upper()
        return any(func in field_upper for func in agg_functions)
    
    def _parse_aggregate_function(self, field: str):
        """Parse aggregate function"""
        field_upper = field.upper()
        
        if 'COUNT(' in field_upper:
            if 'COUNT(*)' in field_upper:
                return 'sum', 1
            else:
                match = re.search(r'COUNT\((\w+)\)', field_upper)
                if match:
                    return 'sum', 1
        elif 'SUM(' in field_upper:
            match = re.search(r'SUM\((\w+)\)', field, re.IGNORECASE)
            if match:
                return 'sum', match.group(1)
        elif 'AVG(' in field_upper:
            match = re.search(r'AVG\((\w+)\)', field, re.IGNORECASE)
            if match:
                return 'avg', match.group(1)
        elif 'MIN(' in field_upper:
            match = re.search(r'MIN\((\w+)\)', field, re.IGNORECASE)
            if match:
                return 'min', match.group(1)
        elif 'MAX(' in field_upper:
            match = re.search(r'MAX\((\w+)\)', field, re.IGNORECASE)
            if match:
                return 'max', match.group(1)
        
        return None, None
    
    def _is_float(self, value: str) -> bool:
        """Check if string represents a float"""
        try:
            float(value)
            return '.' in value
        except ValueError:
            return False


def sql_to_mongo_pipeline(sql_query: str) -> List[Dict[str, Any]]:
    """
    Convenience function to convert SQL to MongoDB aggregation pipeline
    """
    converter = SQLToMongoConverter()
    return converter.convert(sql_query)