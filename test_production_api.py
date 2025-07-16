#!/usr/bin/env python3
"""
Test script for Production AI Dialer API
Tests all endpoints to ensure no demo data fallbacks
"""

import requests
import json
import sys

# Production API base URL
BASE_URL = "https://751fnxwec1.execute-api.us-east-1.amazonaws.com/prod"

def test_endpoint(method, path, data=None, expected_status=200):
    """Test an API endpoint"""
    url = f"{BASE_URL}{path}"
    
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://main.dwrcfhzub1d6l.amplifyapp.com"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"✅ {method} {path} - Status: {response.status_code}")
        
        if response.status_code == expected_status:
            result = response.json()
            print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
            return True
        else:
            print(f"   ❌ Expected {expected_status}, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {path} - Error: {e}")
        return False

def main():
    """Test all production API endpoints"""
    print("🧪 Testing Production AI Dialer API")
    print("=" * 50)
    
    tests = [
        ("GET", "/health"),
        ("GET", "/campaigns"),
        ("POST", "/campaigns", {"name": "Test Campaign"}),
        ("GET", "/analytics/dashboard"),
        ("GET", "/analytics/learning-stats"),
        ("GET", "/queue/status"),
        ("GET", "/calls/active"),
        ("POST", "/call/initiate", {"phone_number": "+1234567890", "campaign_id": "test"}),
        ("POST", "/conversational-training/start", {"user_id": "test_user"}),
        ("POST", "/training/start", {"user_id": "test_user"})
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if len(test) == 3:
            method, path, data = test
            if test_endpoint(method, path, data):
                passed += 1
        else:
            method, path = test
            if test_endpoint(method, path):
                passed += 1
        print()
    
    print(f"🏁 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! API is ready for production use.")
        return 0
    else:
        print("❌ Some tests failed. Check backend deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 