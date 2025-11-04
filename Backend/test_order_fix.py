#!/usr/bin/env python3
"""
Test script to verify that queries maintain original data order
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from App.services.sql_to_mongo_service import SQLToMongoConverter
import json

def test_sql_converter():
    """Test SQL converter with various queries"""
    converter = SQLToMongoConverter()
    
    # Test cases
    test_cases = [
        {
            "name": "Simple SELECT with LIMIT",
            "sql": "SELECT * FROM collection LIMIT 10",
            "expected_sort": True
        },
        {
            "name": "SELECT with WHERE clause",
            "sql": "SELECT * FROM collection WHERE Household_Size > 5 LIMIT 10",
            "expected_sort": True
        },
        {
            "name": "SELECT with explicit ORDER BY",
            "sql": "SELECT * FROM collection ORDER BY Household_Size ASC LIMIT 10",
            "expected_sort": False  # Should not add default sort when explicit sort exists
        },
        {
            "name": "SELECT with ORDER BY DESC",
            "sql": "SELECT * FROM collection ORDER BY Household_Size DESC LIMIT 10",
            "expected_sort": False  # Should not add default sort when explicit sort exists
        },
        {
            "name": "Simple SELECT without LIMIT",
            "sql": "SELECT * FROM collection",
            "expected_sort": True
        }
    ]
    
    print("Testing SQL to MongoDB conversion with proper ordering...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"SQL: {test_case['sql']}")
        
        try:
            pipeline = converter.convert(test_case['sql'])
            print(f"Generated Pipeline: {json.dumps(pipeline, indent=2)}")
            
            # Check if default sort by _id is added appropriately
            has_default_sort = any(
                '$sort' in stage and stage.get('$sort') == {'_id': 1} 
                for stage in pipeline
            )
            
            has_any_sort = any('$sort' in stage for stage in pipeline)
            
            if test_case['expected_sort']:
                if has_default_sort or (not has_any_sort and len(pipeline) == 2 and '$sort' in pipeline[0]):
                    print("✅ PASS: Default sort by _id added correctly")
                else:
                    print("❌ FAIL: Expected default sort by _id but not found")
            else:
                if has_any_sort and not has_default_sort:
                    print("✅ PASS: Explicit sort preserved, no default sort added")
                else:
                    print("❌ FAIL: Expected explicit sort without default sort")
            
        except Exception as e:
            print(f"❌ FAIL: Error converting SQL - {str(e)}")
        
        print("-" * 50)

def test_mongodb_pipeline_modification():
    """Test how MongoDB pipelines would be modified"""
    print("\nTesting MongoDB pipeline modification logic...\n")
    
    test_pipelines = [
        {
            "name": "Simple limit pipeline",
            "pipeline": [{"$limit": 10}],
            "expected": "Should add sort before limit"
        },
        {
            "name": "Match and limit pipeline",
            "pipeline": [{"$match": {"Household_Size": {"$gt": 5}}}, {"$limit": 10}],
            "expected": "Should add sort before limit"
        },
        {
            "name": "Pipeline with existing sort",
            "pipeline": [{"$sort": {"Household_Size": 1}}, {"$limit": 10}],
            "expected": "Should not add default sort"
        },
        {
            "name": "Empty pipeline",
            "pipeline": [],
            "expected": "Should add both sort and limit"
        }
    ]
    
    for i, test_case in enumerate(test_pipelines, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Original Pipeline: {json.dumps(test_case['pipeline'])}")
        
        # Simulate the logic from _execute_aggregation_query
        pipeline = test_case['pipeline'].copy()
        
        # Add default sort by _id to maintain original data order if no sort stage exists
        has_sort = any('$sort' in stage for stage in pipeline)
        if not has_sort:
            # Insert sort stage before any limit stage if it exists
            limit_index = None
            for idx, stage in enumerate(pipeline):
                if '$limit' in stage:
                    limit_index = idx
                    break
            
            if limit_index is not None:
                pipeline.insert(limit_index, {"$sort": {"_id": 1}})
            else:
                pipeline.append({"$sort": {"_id": 1}})
        
        print(f"Modified Pipeline: {json.dumps(pipeline)}")
        print(f"Expected: {test_case['expected']}")
        print("-" * 50)

if __name__ == "__main__":
    test_sql_converter()
    test_mongodb_pipeline_modification()
    print("\nTest completed!")