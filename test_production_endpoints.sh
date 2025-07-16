#!/bin/bash

echo "🧪 Testing Production Endpoints"
echo "================================"

BASE_URL="https://751fnxwec1.execute-api.us-east-1.amazonaws.com/prod"

echo "1. Testing Health Endpoint..."
curl -s "$BASE_URL/health" | jq .

echo -e "\n2. Testing Analytics Dashboard..."
curl -s "$BASE_URL/analytics/dashboard" | jq .

echo -e "\n3. Testing Learning Stats..."
curl -s "$BASE_URL/analytics/learning-stats" | jq .

echo -e "\n4. Testing Conversational Training Start..."
curl -s -X POST -H "Content-Type: application/json" -d '{"user_id": "test-user"}' "$BASE_URL/conversational-training/start" | jq .

echo -e "\n5. Testing Conversational Training Continue..."
SESSION_ID=$(curl -s -X POST -H "Content-Type: application/json" -d '{"user_id": "test-user"}' "$BASE_URL/conversational-training/start" | jq -r '.session_id')
curl -s -X POST -H "Content-Type: application/json" -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"Lead Generation\"}" "$BASE_URL/conversational-training/continue" | jq .

echo -e "\n✅ All tests completed!" 