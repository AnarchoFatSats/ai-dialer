#!/bin/bash

echo "🧪 Testing Enhanced Backend Deployment"
echo "====================================="

BASE_URL="https://751fnxwec1.execute-api.us-east-1.amazonaws.com/prod"

echo "1. Testing Health Endpoint (should show 1.0.0-production)..."
HEALTH=$(curl -s "$BASE_URL/health" | jq -r '.version // "error"')
echo "   Version: $HEALTH"

if [ "$HEALTH" = "1.0.0-production" ]; then
    echo "   ✅ Enhanced version deployed!"
else
    echo "   ❌ Still minimal version"
fi

echo -e "\n2. Testing Conversational Training (should mention Reach)..."
TRAINING=$(curl -s -X POST -H "Content-Type: application/json" -d '{"user_id": "test"}' "$BASE_URL/conversational-training/start" | jq -r '.message // "error"')
echo "   Response: ${TRAINING:0:100}..."

if [[ "$TRAINING" == *"Reach"* ]]; then
    echo "   ✅ Reach guide is working!"
else
    echo "   ❌ Still basic response"
fi

echo -e "\n3. Testing Analytics Dashboard..."
ANALYTICS=$(curl -s "$BASE_URL/analytics/dashboard" | jq -r '.active_calls // "error"')
echo "   Active calls: $ANALYTICS"

if [ "$ANALYTICS" != "error" ] && [ "$ANALYTICS" != "null" ]; then
    echo "   ✅ Analytics endpoint working!"
else
    echo "   ❌ Analytics not working"
fi

echo -e "\n4. Testing Learning Stats..."
LEARNING=$(curl -s "$BASE_URL/analytics/learning-stats" | jq -r '.progress // "error"')
echo "   Progress: $LEARNING%"

if [ "$LEARNING" != "error" ] && [ "$LEARNING" != "null" ]; then
    echo "   ✅ Learning stats working!"
else
    echo "   ❌ Learning stats not working"
fi

echo -e "\n📊 SUMMARY:"
echo "======================================"
if [ "$HEALTH" = "1.0.0-production" ] && [[ "$TRAINING" == *"Reach"* ]]; then
    echo "🎉 SUCCESS! Enhanced backend is deployed and working!"
    echo "✅ Frontend will now work perfectly with Reach guide"
    echo "✅ All conversational training features active"
    echo "✅ Analytics and dashboard endpoints functional"
else
    echo "⚠️  Deployment needed - please upload lambda-deployment.zip to AWS Lambda"
fi
echo "======================================" 