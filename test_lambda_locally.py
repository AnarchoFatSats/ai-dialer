#!/usr/bin/env python3

import json
import sys
import os

# Add the lambda package to the path
sys.path.insert(0, 'lambda-package')

from lambda_handler import lambda_handler

class MockContext:
    def __init__(self):
        self.function_name = "test-function"
        self.function_version = "$LATEST"
        self.memory_limit_in_mb = 512
        self.aws_request_id = "test-request-id"

def test_conversational_training():
    """Test the conversational training endpoints"""
    
    print("🧪 Testing Conversational Training Endpoints...")
    
    # Test 1: Start conversation
    print("\n1. Testing /conversational-training/start...")
    event = {
        "path": "/conversational-training/start",
        "httpMethod": "POST",
        "body": json.dumps({"user_id": "test-user"})
    }
    
    result = lambda_handler(event, MockContext())
    print(f"Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        print(f"✅ Success! Session ID: {body['session_id']}")
        print(f"Message: {body['message'][:100]}...")
        print(f"Suggested responses: {body['suggested_responses']}")
        session_id = body['session_id']
    else:
        print(f"❌ Failed: {result['body']}")
        return
    
    # Test 2: Continue conversation with Lead Generation
    print("\n2. Testing /conversational-training/continue with 'Lead Generation'...")
    event = {
        "path": "/conversational-training/continue",
        "httpMethod": "POST",
        "body": json.dumps({
            "session_id": session_id,
            "message": "Lead Generation"
        })
    }
    
    result = lambda_handler(event, MockContext())
    print(f"Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        print(f"✅ Success! Response: {body['message'][:100]}...")
        print(f"Suggested responses: {body['suggested_responses']}")
    else:
        print(f"❌ Failed: {result['body']}")
        return
    
    # Test 3: Continue conversation with Homeowners
    print("\n3. Testing /conversational-training/continue with 'Homeowners'...")
    event = {
        "path": "/conversational-training/continue",
        "httpMethod": "POST",
        "body": json.dumps({
            "session_id": session_id,
            "message": "Homeowners"
        })
    }
    
    result = lambda_handler(event, MockContext())
    print(f"Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        print(f"✅ Success! Response: {body['message'][:100]}...")
        print(f"Suggested responses: {body['suggested_responses']}")
    else:
        print(f"❌ Failed: {result['body']}")

def test_analytics_endpoints():
    """Test the analytics endpoints"""
    
    print("\n🧪 Testing Analytics Endpoints...")
    
    # Test dashboard endpoint
    print("\n1. Testing /analytics/dashboard...")
    event = {
        "path": "/analytics/dashboard",
        "httpMethod": "GET"
    }
    
    result = lambda_handler(event, MockContext())
    print(f"Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        print(f"✅ Success! Active calls: {body['active_calls']}")
        print(f"Today's transfers: {body['today_transfers']}")
        print(f"Today's revenue: ${body['today_revenue']}")
    else:
        print(f"❌ Failed: {result['body']}")
    
    # Test learning stats endpoint
    print("\n2. Testing /analytics/learning-stats...")
    event = {
        "path": "/analytics/learning-stats",
        "httpMethod": "GET"
    }
    
    result = lambda_handler(event, MockContext())
    print(f"Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        print(f"✅ Success! Progress: {body['progress']}%")
        print(f"Success rate: {body['successRate']}%")
        print(f"Total calls: {body['totalCalls']}")
    else:
        print(f"❌ Failed: {result['body']}")

def test_health_endpoint():
    """Test the health endpoint"""
    
    print("\n🧪 Testing Health Endpoint...")
    
    event = {
        "path": "/health",
        "httpMethod": "GET"
    }
    
    result = lambda_handler(event, MockContext())
    print(f"Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        print(f"✅ Success! Status: {body['status']}")
        print(f"Version: {body['version']}")
        print(f"Environment: {body['environment']}")
    else:
        print(f"❌ Failed: {result['body']}")

if __name__ == "__main__":
    print("🚀 Testing Enhanced Lambda Handler")
    print("=" * 50)
    
    test_health_endpoint()
    test_analytics_endpoints()
    test_conversational_training()
    
    print("\n✅ All tests completed!") 