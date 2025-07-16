#!/usr/bin/env python3
"""
Verify Production Fix - Confirms all systems working
Run this AFTER deploying lambda-deployment-fixed.zip
"""

import requests
import json
import time

BASE_URL = "https://751fnxwec1.execute-api.us-east-1.amazonaws.com/prod"

def verify_fix():
    print("🔍 VERIFYING PRODUCTION FIX")
    print("=" * 50)
    
    # Test 1: Health Check
    print("1. Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("version") == "1.0.0-production":
                print("   ✅ Health check FIXED - Production version running")
            else:
                print("   ❌ Still running old version")
                return False
        else:
            print("   ❌ Health check failed")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 2: CORS Headers
    print("2. Testing CORS Headers...")
    try:
        headers = {"Origin": "https://main.dwrcfhzub1d6l.amplifyapp.com"}
        response = requests.get(f"{BASE_URL}/health", headers=headers, timeout=10)
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        if cors_header == "https://main.dwrcfhzub1d6l.amplifyapp.com":
            print("   ✅ CORS FIXED - Specific domain allowed")
        else:
            print(f"   ❌ CORS issue - Got: {cors_header}")
            return False
    except Exception as e:
        print(f"   ❌ CORS test error: {e}")
        return False
    
    # Test 3: Critical Endpoints
    print("3. Testing Critical Endpoints...")
    endpoints = [
        ("/campaigns", "GET"),
        ("/analytics/dashboard", "GET"),
        ("/queue/status", "GET"),
        ("/calls/active", "GET")
    ]
    
    for path, method in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {path} - Working")
            else:
                print(f"   ❌ {path} - Status {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ {path} - Error: {e}")
            return False
    
    # Test 4: Campaign Creation
    print("4. Testing Campaign Creation...")
    try:
        data = {"name": "Production Test Campaign"}
        response = requests.post(f"{BASE_URL}/campaigns", json=data, timeout=10)
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   ✅ Campaign created: {result.get('name')}")
        else:
            print(f"   ❌ Campaign creation failed - Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Campaign creation error: {e}")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("Frontend should now work without errors.")
    print("Go refresh your Amplify app: https://main.dwrcfhzub1d6l.amplifyapp.com")
    return True

if __name__ == "__main__":
    if verify_fix():
        print("\n✅ PRODUCTION FIX SUCCESSFUL!")
        exit(0)
    else:
        print("\n❌ PRODUCTION FIX FAILED!")
        print("Check AWS Lambda deployment of lambda-deployment-fixed.zip")
        exit(1) 