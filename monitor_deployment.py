#!/usr/bin/env python3
"""
Monitor Lambda Deployment
Checks if the fix was deployed successfully
"""

import requests
import time
import sys

BASE_URL = "https://751fnxwec1.execute-api.us-east-1.amazonaws.com/prod"

def check_deployment():
    """Check if the new version is deployed"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            version = data.get("version", "unknown")
            status = data.get("status", "unknown")
            
            if version == "1.0.0-production":
                return True, f"✅ FIXED! Version: {version}, Status: {status}"
            else:
                return False, f"⏳ Still old version: {version}"
        else:
            return False, f"❌ Health check failed: {response.status_code}"
    except Exception as e:
        return False, f"❌ Connection error: {e}"

def monitor():
    """Monitor deployment status"""
    print("🔍 MONITORING DEPLOYMENT STATUS")
    print("Checking every 10 seconds for the fix...")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    attempt = 1
    
    while True:
        try:
            is_fixed, message = check_deployment()
            
            print(f"[Attempt {attempt}] {message}")
            
            if is_fixed:
                print("\n🎉 DEPLOYMENT SUCCESSFUL!")
                print("Run: python3 verify_production_fix.py")
                print("Then refresh your frontend!")
                return True
            
            attempt += 1
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped by user")
            return False

if __name__ == "__main__":
    monitor() 