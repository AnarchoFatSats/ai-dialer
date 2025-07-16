#!/bin/bash

# 🎯 AI Dialer Enhanced Backend Verification
# Run this after deploying lambda-deployment.zip

API_BASE="https://751fnxwec1.execute-api.us-east-1.amazonaws.com/prod"

echo "🚀 Testing Enhanced AI Dialer Backend Deployment"
echo "=================================================="

echo ""
echo "📍 1. Testing Health Endpoint (should show production version)"
curl -s "$API_BASE/health" | python3 -m json.tool
echo ""

echo "📍 2. Testing Analytics Dashboard (should show real data)"
curl -s "$API_BASE/analytics/dashboard" | python3 -m json.tool
echo ""

echo "📍 3. Testing Conversational Training (should show Reach intro)"
curl -s "$API_BASE/conversational-training/start" | python3 -m json.tool
echo ""

echo "📍 4. Testing Learning Stats (should show analytics)"
curl -s "$API_BASE/analytics/learning-stats" | python3 -m json.tool
echo ""

echo "=================================================="
echo "✅ If you see production data above, deployment successful!"
echo "🎯 Frontend will now work with full Reach conversational guide"
echo "==================================================" 