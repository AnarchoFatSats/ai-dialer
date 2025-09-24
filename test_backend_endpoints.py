#!/usr/bin/env python3
"""
AI Dialer Backend Endpoint Testing Script
=========================================

Tests all implemented endpoints to verify functionality.
Run this to confirm the backend is working correctly.
"""

from app.main import app
from fastapi.testclient import TestClient
import json
import sys

def test_endpoints():
    """Test all implemented endpoints."""
    print("🚀 AI DIALER BACKEND ENDPOINT TESTING")
    print("=" * 50)

    client = TestClient(app)
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }

    # Test Categories
    test_categories = {
        "System Health": [
            ("/health", "Health Check"),
            ("/live", "Liveness Check"),
        ],
        "Analytics": [
            ("/analytics/real-time-stats", "Real-time Stats"),
            ("/analytics/hourly-performance", "Hourly Performance"),
            ("/analytics/revenue-tracking", "Revenue Tracking"),
            ("/analytics/conversion-funnel", "Conversion Funnel"),
            ("/analytics/call-quality-metrics", "Call Quality Metrics"),
            ("/analytics/agent-performance", "Agent Performance"),
            ("/analytics/system-health", "System Health"),
        ],
        "Cost Optimization": [
            ("/cost/real-time-spending", "Real-time Spending"),
            ("/cost/budget-status", "Budget Status"),
            ("/cost/profit-analysis", "Profit Analysis"),
            ("/cost/api-breakdown", "API Cost Breakdown"),
            ("/cost/cost-per-transfer", "Cost Per Transfer"),
            ("/cost/roi-analysis", "ROI Analysis"),
            ("/cost/billing-history", "Billing History"),
            ("/cost/daily-spending", "Daily Spending"),
            ("/cost/predictions", "Cost Predictions"),
        ],
        "Call Orchestration": [
            ("/calls/live-monitoring", "Live Call Monitoring"),
            ("/calls/capacity-status", "Capacity Status"),
            ("/calls/statistics", "Call Statistics"),
            ("/calls/scheduled", "Scheduled Calls"),
            ("/calls/agent-queue", "Agent Queue"),
            ("/queue/status", "Queue Status"),
        ],
        "Campaign Management (Synthetic)": [
            ("/campaigns/123-456/schedule", "Campaign Schedule"),
            ("/campaigns/123-456/ab-test", "A/B Test Results"),
        ]
    }

    all_endpoints = []
    for category, endpoints in test_categories.items():
        all_endpoints.extend(endpoints)

    total_endpoints = len(all_endpoints)

    for category, endpoints in test_categories.items():
        print(f"\n📋 {category}:")
        print("-" * (len(category) + 4))

        for endpoint, description in endpoints:
            results["total"] += 1
            try:
                response = client.get(endpoint)
                if response.status_code == 200:
                    print(f"  ✅ {description}: {response.status_code}")
                    results["passed"] += 1
                else:
                    print(f"  ❌ {description}: {response.status_code}")
                    results["failed"] += 1
            except Exception as e:
                print(f"  ❌ {description}: ERROR")
                results["failed"] += 1

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Total Endpoints: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"🎯 Success Rate: {results['passed']/results['total']*100:.1f}%")

    if results["failed"] == 0:
        print("🎉 ALL ENDPOINTS WORKING PERFECTLY!")
        print("🚀 Backend is ready for production!")
        return True
    else:
        print(f"⚠️  {results['failed']} endpoints need attention")
        return False

def test_sample_data():
    """Test sample data from key endpoints."""
    print("\n" + "=" * 50)
    print("📋 SAMPLE DATA FROM KEY ENDPOINTS")
    print("=" * 50)

    client = TestClient(app)

    # Test real-time stats
    print("\n🔴 Real-time Stats:")
    response = client.get("/analytics/real-time-stats")
    if response.status_code == 200:
        data = response.json()
        print(f"  Today Calls: {data['data']['today_calls']}")
        print(f"  Today Transfers: {data['data']['today_transfers']}")
        print(f"  Today Revenue: ${data['data']['today_revenue']:.2f}")
        print(f"  Active Campaigns: {data['data']['active_campaigns']}")

    # Test cost per transfer
    print("\n💰 Cost Per Transfer:")
    response = client.get("/cost/cost-per-transfer")
    if response.status_code == 200:
        data = response.json()
        print(f"  Current CPT: ${data['data']['overall_cost_per_transfer']:.2f}")
        print(f"  Target CPT: ${data['data']['target_cost_per_transfer']:.2f}")
        print(f"  Trend: {data['data']['cost_trend']}")

    # Test system health
    print("\n🏥 System Health:")
    response = client.get("/analytics/system-health")
    if response.status_code == 200:
        data = response.json()
        print(f"  Overall Status: {data['data']['overall_status']}")
        print(f"  Uptime: {data['data']['uptime']}")
        print(f"  CPU Usage: {data['data']['resource_utilization']['cpu_percent']}%")
        print(f"  Memory Usage: {data['data']['resource_utilization']['memory_percent']}%")

if __name__ == "__main__":
    success = test_endpoints()
    test_sample_data()

    if success:
        print("\n🎉 BACKEND TESTING COMPLETE - ALL SYSTEMS GO!")
        sys.exit(0)
    else:
        print("\n⚠️  BACKEND TESTING COMPLETE - SOME ISSUES FOUND")
        sys.exit(1)
