#!/usr/bin/env python3
"""
Simple test script to verify NLP functionality with Gemini API
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_api():
    """Test basic Gemini API connectivity"""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        return False
    
    print(f"✅ Found Gemini API key: {api_key[:10]}...")
    
    # Test basic API call
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": "Say hello in JSON format"}]}],
        "generationConfig": {
            "temperature": 0.1,
            "topK": 1,
            "topP": 1,
            "maxOutputTokens": 100,
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            response_json = response.json()
            if "candidates" in response_json:
                print("✅ Gemini API is working correctly")
                return True
        else:
            print(f"❌ Gemini API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Gemini API connection failed: {str(e)}")
        return False

def test_nl_to_mongo_conversion():
    """Test natural language to MongoDB conversion"""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ Cannot test NL conversion without API key")
        return False
    
    # Sample schema
    schema = {
        "name": "string",
        "age": "number", 
        "salary": "number",
        "department": "string",
        "employment_status": "string"
    }
    
    # Sample natural language query
    nl_query = "Show me the average salary by department"
    
    prompt = f"""
    You are an expert data analyst who translates natural language questions into executable MongoDB Aggregation Pipeline queries.
    Your response MUST be ONLY the JSON for the MongoDB aggregation pipeline, represented as a valid JSON array string. 
    Do not include any explanations, markdown formatting, code blocks, or any text other than the JSON array itself.

    Dataset Schema (field names and types):
    {json.dumps(schema, indent=2)}

    User Question:
    "{nl_query}"

    Rules:
    1. Return ONLY a valid JSON array representing the MongoDB aggregation pipeline
    2. Use exact field names from the schema provided
    3. For aggregations, use appropriate MongoDB operators like $group, $match, $sort, $limit
    4. Always include a reasonable $limit (like 100) unless specifically asked for all data

    Example format:
    [{{"$group": {{"_id": "$department", "average_salary": {{"$avg": "$salary"}}}}}}, {{"$limit": 100}}]
    """
    
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
    
    try:
        print(f"🔍 Testing NL query: '{nl_query}'")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API request failed: {response.status_code} - {response.text}")
            return False
            
        response_json = response.json()
        
        if "error" in response_json:
            print(f"❌ API error: {response_json['error']}")
            return False
        
        # Extract generated text
        generated_text = ""
        if "candidates" in response_json and len(response_json["candidates"]) > 0:
            candidate = response_json["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        generated_text += part["text"]
        
        print(f"🤖 Generated response: {generated_text}")
        
        # Clean up response
        cleaned_text = generated_text.strip()
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text.split('```json')[1]
        if cleaned_text.startswith('```'):
            cleaned_text = cleaned_text.split('```')[1]
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text.rsplit('```', 1)[0]
        cleaned_text = cleaned_text.strip()
        
        # Validate JSON
        try:
            mongo_query = json.loads(cleaned_text)
            print(f"✅ Successfully generated MongoDB query: {json.dumps(mongo_query, indent=2)}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Generated text is not valid JSON: {e}")
            print(f"Raw text: {cleaned_text}")
            return False
            
    except Exception as e:
        print(f"❌ NL conversion test failed: {str(e)}")
        return False

def main():
    print("🧪 Testing Query Mitra NLP Functionality")
    print("=" * 50)
    
    # Test 1: Basic API connectivity
    print("\n1. Testing Gemini API connectivity...")
    api_works = test_gemini_api()
    
    if not api_works:
        print("\n❌ Basic API test failed. Please check your GEMINI_API_KEY.")
        return
    
    # Test 2: NL to MongoDB conversion
    print("\n2. Testing Natural Language to MongoDB conversion...")
    conversion_works = test_nl_to_mongo_conversion()
    
    if conversion_works:
        print("\n🎉 All tests passed! Your NLP functionality is ready to use.")
        print("\nYou can now:")
        print("- Start your backend server: python run.py")
        print("- Start your frontend: npm run dev")
        print("- Upload a dataset and try natural language queries like:")
        print("  • 'Show me the average income by state'")
        print("  • 'Find all records where age is greater than 30'") 
        print("  • 'What is the total count by category?'")
    else:
        print("\n❌ NL conversion test failed. Please check your implementation.")

if __name__ == "__main__":
    main()