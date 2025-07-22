#!/bin/bash
# AI Dialer Frontend - Backend URL Update Script
# Use this script to update the backend URL when ECS IP changes

echo "🔍 Discovering current ECS backend IP..."

# Get current ECS IP from test script
cd ..
CURRENT_IP=$(python3 test-production-ai-ecs.py 2>/dev/null | grep "Testing AI Dialer at:" | cut -d' ' -f6 | cut -d':' -f2 | tr -d '/')

if [ -z "$CURRENT_IP" ]; then
    echo "❌ Could not discover current ECS IP"
    echo "💡 Manually run: python3 test-production-ai-ecs.py"
    exit 1
fi

NEW_URL="http://$CURRENT_IP:8000"
echo "✅ Current backend: $NEW_URL"

# Update the environment configuration
cd amplify_ui
echo "🔧 Updating frontend configuration..."

# Update environment.js
sed -i.bak "s|http://[0-9.]*:8000|$NEW_URL|g" src/config/environment.js

if [ $? -eq 0 ]; then
    echo "✅ Updated src/config/environment.js"
    echo "🔗 New backend URL: $NEW_URL"
    echo ""
    echo "🚀 Ready to restart frontend with:"
    echo "   npm start"
else
    echo "❌ Failed to update configuration"
    exit 1
fi 