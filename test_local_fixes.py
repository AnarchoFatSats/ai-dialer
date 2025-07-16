#!/usr/bin/env python3
"""
Test script to verify the Lambda fixes work correctly
"""
import asyncio
import json
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

async def test_endpoints():
    """Test the fixed endpoints"""
    print("🧪 Testing Enhanced Lambda Fixes")
    print("=" * 40)
    
    try:
        # Set up environment for testing
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
        os.environ["ENVIRONMENT"] = "production"
        os.environ["DEBUG"] = "false"
        
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Health endpoint
        print("1. Testing /health...")
        total_tests += 1
        try:
            response = client.get("/health")
            if response.status_code == 200:
                print("   ✅ Health endpoint working")
                tests_passed += 1
            else:
                print(f"   ❌ Health returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ Health failed: {e}")
        
        # Test 2: Campaigns list
        print("2. Testing GET /campaigns...")
        total_tests += 1
        try:
            response = client.get("/campaigns")
            if response.status_code == 200:
                data = response.json()
                if "campaigns" in data:
                    print("   ✅ Campaigns endpoint working")
                    tests_passed += 1
                else:
                    print("   ❌ Campaigns missing data structure")
            else:
                print(f"   ❌ Campaigns returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ Campaigns failed: {e}")
        
        # Test 3: Create campaign
        print("3. Testing POST /campaigns...")
        total_tests += 1
        try:
            campaign_data = {
                "name": "Test Campaign",
                "script_template": "Hello, this is a test"
            }
            response = client.post("/campaigns", json=campaign_data)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("   ✅ Create campaign working")
                    tests_passed += 1
                else:
                    print("   ❌ Create campaign returned error")
            else:
                print(f"   ❌ Create campaign returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ Create campaign failed: {e}")
        
        # Test 4: Analytics dashboard
        print("4. Testing /analytics/dashboard...")
        total_tests += 1
        try:
            response = client.get("/analytics/dashboard")
            if response.status_code == 200:
                data = response.json()
                if "active_calls" in data:
                    print("   ✅ Dashboard endpoint working")
                    tests_passed += 1
                else:
                    print("   ❌ Dashboard missing data structure")
            else:
                print(f"   ❌ Dashboard returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ Dashboard failed: {e}")
        
        # Test 5: Queue status
        print("5. Testing /queue/status...")
        total_tests += 1
        try:
            response = client.get("/queue/status")
            if response.status_code == 200:
                data = response.json()
                if "queue_size" in data:
                    print("   ✅ Queue status working")
                    tests_passed += 1
                else:
                    print("   ❌ Queue status missing data")
            else:
                print(f"   ❌ Queue status returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ Queue status failed: {e}")
        
        # Test 6: Call initiate
        print("6. Testing POST /call/initiate...")
        total_tests += 1
        try:
            call_data = {"campaign_id": "test-123"}
            response = client.post("/call/initiate", json=call_data)
            if response.status_code == 200:
                data = response.json()
                if "call_id" in data:
                    print("   ✅ Call initiate working")
                    tests_passed += 1
                else:
                    print("   ❌ Call initiate missing data")
            else:
                print(f"   ❌ Call initiate returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ Call initiate failed: {e}")
        
        # Test 7: Training start
        print("7. Testing POST /training/start...")
        total_tests += 1
        try:
            response = client.post("/training/start", json={})
            if response.status_code == 200:
                data = response.json()
                if "session_id" in data and "Reach" in data.get("message", ""):
                    print("   ✅ Training start working with Reach")
                    tests_passed += 1
                else:
                    print("   ❌ Training start missing Reach guide")
            else:
                print(f"   ❌ Training start returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ Training start failed: {e}")
        
        print("\n" + "=" * 40)
        print(f"🏁 Test Results: {tests_passed}/{total_tests} passed")
        
        if tests_passed == total_tests:
            print("🎉 ALL TESTS PASSED! Ready to deploy enhanced version!")
            return True
        else:
            print("❌ Some tests failed. Check the issues above.")
            return False
            
    except Exception as e:
        print(f"💥 Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_endpoints())
    sys.exit(0 if result else 1) 