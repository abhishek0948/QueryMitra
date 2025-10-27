"""
Test script for SQL to MongoDB converter.
Run this to validate the conversion functionality.
"""

from App.services.sql_to_mongo_service import SQLToMongoConverter
import json

def test_sql_converter():
    converter = SQLToMongoConverter()
    
    test_cases = [
        # Basic SELECT queries
        {
            "sql": "SELECT * FROM users LIMIT 10",
            "description": "Simple SELECT ALL with LIMIT"
        },
        {
            "sql": "SELECT name, age, city FROM users",
            "description": "SELECT specific columns"
        },
        
        # WHERE clause tests
        {
            "sql": "SELECT * FROM users WHERE age > 25",
            "description": "WHERE with greater than"
        },
        {
            "sql": "SELECT name FROM users WHERE age >= 18 AND city = 'Mumbai'",
            "description": "WHERE with AND condition"
        },
        {
            "sql": "SELECT * FROM users WHERE salary > 50000 OR department = 'HR'",
            "description": "WHERE with OR condition"
        },
        {
            "sql": "SELECT * FROM products WHERE name LIKE '%phone%'",
            "description": "WHERE with LIKE operator"
        },
        {
            "sql": "SELECT * FROM users WHERE city IN ('Mumbai', 'Delhi', 'Bangalore')",
            "description": "WHERE with IN operator"
        },
        {
            "sql": "SELECT * FROM users WHERE age NOT IN (25, 30, 35)",
            "description": "WHERE with NOT IN operator"
        },
        
        # GROUP BY tests
        {
            "sql": "SELECT city, COUNT(*) FROM users GROUP BY city",
            "description": "GROUP BY with COUNT"
        },
        {
            "sql": "SELECT department, AVG(salary) FROM employees GROUP BY department",
            "description": "GROUP BY with AVG"
        },
        {
            "sql": "SELECT city, MAX(age), MIN(age) FROM users GROUP BY city",
            "description": "GROUP BY with multiple aggregates"
        },
        
        # ORDER BY tests
        {
            "sql": "SELECT * FROM users ORDER BY age DESC LIMIT 5",
            "description": "ORDER BY DESC with LIMIT"
        },
        {
            "sql": "SELECT name, salary FROM employees ORDER BY salary ASC, name DESC",
            "description": "ORDER BY multiple columns"
        },
        
        # Complex queries
        {
            "sql": "SELECT city, AVG(age) as avg_age FROM users WHERE age > 18 GROUP BY city HAVING AVG(age) > 25 ORDER BY avg_age DESC LIMIT 10",
            "description": "Complex query with all clauses"
        },
        {
            "sql": "SELECT department, COUNT(*) as employee_count, AVG(salary) as avg_salary FROM employees WHERE salary > 30000 GROUP BY department ORDER BY employee_count DESC",
            "description": "Complex aggregation query"
        }
    ]
    
    print("🧪 Testing SQL to MongoDB Converter")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        print(f"SQL: {test_case['sql']}")
        
        try:
            pipeline = converter.convert(test_case['sql'])
            print("✅ MongoDB Pipeline:")
            print(json.dumps(pipeline, indent=2))
            passed += 1
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            failed += 1
        
        print("-" * 40)
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed)) * 100:.1f}%")

if __name__ == "__main__":
    test_sql_converter()