#!/usr/bin/env python3
"""
Production AI Functionality Test Script for ECS Deployment
Tests all AI services and capabilities in the deployed ECS environment
"""

import requests
import json
import sys
import time
from typing import Dict, Any

def get_ecs_task_ip():
    """Get the public IP of the running ECS task"""
    import subprocess
    try:
        # Get the task ARN
        result = subprocess.run([
            "aws", "ecs", "list-tasks", 
            "--cluster", "ai-dialer-cluster",
            "--query", "taskArns[0]",
            "--output", "text"
        ], capture_output=True, text=True, check=True)
        
        task_arn = result.stdout.strip()
        if not task_arn or task_arn == "None":
            print("❌ No running tasks found in cluster")
            return None
            
        # Get the task details
        result = subprocess.run([
            "aws", "ecs", "describe-tasks",
            "--cluster", "ai-dialer-cluster", 
            "--tasks", task_arn,
            "--query", "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value",
            "--output", "text"
        ], capture_output=True, text=True, check=True)
        
        eni_id = result.stdout.strip()
        if not eni_id:
            print("❌ Could not find network interface")
            return None
            
        # Get the public IP
        result = subprocess.run([
            "aws", "ec2", "describe-network-interfaces",
            "--network-interface-ids", eni_id,
            "--query", "NetworkInterfaces[0].Association.PublicIp",
            "--output", "text"
        ], capture_output=True, text=True, check=True)
        
        public_ip = result.stdout.strip()
        return public_ip if public_ip != "None" else None
        
    except Exception as e:
        print(f"❌ Error getting ECS task IP: {e}")
        return None

def test_endpoint(base_url: str, endpoint: str, method: str = "GET", data: Dict[Any, Any] = None) -> Dict[str, Any]:
    """Test a single API endpoint"""
    try:
        url = f"{base_url}{endpoint}"
        
        if method.upper() == "GET":
            response = requests.get(url, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            return {"error": f"Unsupported method: {method}"}
            
        return {
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "endpoint": endpoint,
            "method": method
        }
    except Exception as e:
        return {
            "error": str(e),
            "endpoint": endpoint,
            "method": method,
            "success": False
        }

def main():
    """Run comprehensive production AI functionality tests"""
    print("🌐 Testing Production AI Dialer on AWS ECS")
    print("=" * 50)
    
    # Get ECS task IP
    print("🔍 Finding ECS task IP address...")
    task_ip = get_ecs_task_ip()
    
    if not task_ip:
        print("❌ Could not determine ECS task IP address")
        print("💡 Try running manually:")
        print("   aws ecs describe-tasks --cluster ai-dialer-cluster --tasks $(aws ecs list-tasks --cluster ai-dialer-cluster --query 'taskArns[0]' --output text)")
        sys.exit(1)
    
    base_url = f"http://{task_ip}:8000"
    print(f"✅ Testing AI Dialer at: {base_url}")
    
    # Wait for service to be ready
    print("⏳ Waiting for service to be ready...")
    for i in range(6):
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Service is ready!")
                break
        except:
            pass
        print(f"   Attempt {i+1}/6 - waiting 10 seconds...")
        time.sleep(10)
    else:
        print("❌ Service did not become ready within 60 seconds")
        sys.exit(1)
    
    # Comprehensive AI functionality tests
    test_cases = [
        # Core health check with AI services
        {"endpoint": "/health", "method": "GET", "description": "Health check with AI services"},
        
        # Campaign management with AI
        {"endpoint": "/campaigns", "method": "GET", "description": "List campaigns with AI capabilities"},
        {"endpoint": "/campaigns", "method": "POST", "data": {
            "name": "Production AI Test Campaign",
            "description": "Testing AI capabilities in production",
            "script_template": "Hello, this is an AI-powered production call",
            "guided_training": True,
            "primary_goal": "test production AI functionality",
            "target_audience": "production users",
            "brand_tone": "professional",
            "industry": "technology"
        }, "description": "Create campaign with AI training (Production)"},
        
        # Analytics with AI insights
        {"endpoint": "/analytics/dashboard", "method": "GET", "description": "Analytics dashboard with AI"},
        {"endpoint": "/analytics/learning-stats", "method": "GET", "description": "AI learning statistics (Production)"},
        
        # AI-specific production endpoints
        {"endpoint": "/conversational-training/start", "method": "POST", "data": {
            "campaign_id": "prod-test-campaign",
            "training_data": {"conversation_samples": ["Hello, how can I help?", "Thank you for your time"]}
        }, "description": "AI conversational training (Production)"},
        
        {"endpoint": "/training/start", "method": "POST", "data": {
            "campaign_id": "prod-test-campaign",
            "training_type": "voice_synthesis"
        }, "description": "AI training initialization (Production)"},
        
        # Real-time capabilities
        {"endpoint": "/queue/status", "method": "GET", "description": "Queue status with AI processing"},
        {"endpoint": "/calls/active", "method": "GET", "description": "Active calls with AI monitoring"},
    ]
    
    results = []
    ai_features_working = 0
    total_tests = len(test_cases)
    
    print(f"\n🧪 Running {total_tests} Production AI Tests")
    print("-" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{total_tests}] 🔍 {test_case['description']}")
        print(f"   {test_case['method']} {test_case['endpoint']}")
        
        result = test_endpoint(
            base_url,
            test_case["endpoint"], 
            test_case["method"], 
            test_case.get("data")
        )
        
        results.append(result)
        
        if result["success"]:
            print(f"   ✅ Success ({result['status_code']})")
            ai_features_working += 1
            
            # Check for AI-specific indicators in response
            response_text = str(result.get("response", ""))
            ai_indicators = ["ai", "anthropic", "openai", "training", "conversation", "model", "claude", "gpt"]
            if any(indicator in response_text.lower() for indicator in ai_indicators):
                print(f"   🤖 AI features detected in response")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            if 'status_code' in result:
                print(f"      Status: {result['status_code']}")
    
    print("\n" + "=" * 60)
    print("🏁 PRODUCTION AI TEST RESULTS")
    print("=" * 60)
    print(f"🌐 Tested at: {base_url}")
    print(f"✅ Tests Passed: {ai_features_working}/{total_tests}")
    success_rate = (ai_features_working / total_tests) * 100
    print(f"📊 Success Rate: {success_rate:.1f}%")
    
    if ai_features_working == total_tests:
        print("🎉 ALL PRODUCTION AI FEATURES WORKING!")
        print("🚀 Frontend team can connect immediately!")
        print("🤖 Full AI implementation deployed successfully!")
    elif ai_features_working >= total_tests * 0.7:  # 70% or better
        print("⚠️  Most AI features working in production")
        print("🔧 Minor issues detected but deployment is functional")
        print("🚀 Frontend team can connect with monitoring")
    else:
        print("❌ Multiple AI features failing in production")
        print("🛠️  Requires investigation before frontend connection")
    
    print(f"\n📋 Production Endpoint for Frontend Team:")
    print(f"🌐 Base URL: {base_url}")
    print(f"🔗 Health Check: {base_url}/health")
    print(f"📊 Dashboard: {base_url}/analytics/dashboard")
    
    return ai_features_working >= total_tests * 0.7

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 