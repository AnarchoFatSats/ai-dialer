#!/bin/bash

# 🚀 Frontend Deployment Script for AI Dialer
# This script deploys the integrated frontend to AWS Amplify

set -e

echo "🔧 Starting AI Dialer Frontend Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend URL is set
if [ -z "$REACT_APP_BACKEND_API_URL" ]; then
    echo -e "${YELLOW}⚠️  Warning: REACT_APP_BACKEND_API_URL not set${NC}"
    echo "Setting default to http://localhost:8000"
    export REACT_APP_BACKEND_API_URL="http://localhost:8000"
fi

# Navigate to frontend directory
cd amplify_ui

echo "📦 Installing dependencies..."
npm install

echo "🔍 Running build..."
npm run build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build completed successfully!${NC}"
else
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

echo "🚀 Deploying to AWS Amplify..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI first.${NC}"
    exit 1
fi

# Deploy to Amplify
if [ -f "deploy-to-amplify.sh" ]; then
    chmod +x deploy-to-amplify.sh
    ./deploy-to-amplify.sh
else
    echo -e "${YELLOW}⚠️  deploy-to-amplify.sh not found. Manual deployment required.${NC}"
    echo "Build files are ready in the 'build' directory."
fi

echo -e "${GREEN}🎉 Frontend deployment completed!${NC}"
echo ""
echo "📋 Post-deployment checklist:"
echo "1. ✅ Update REACT_APP_BACKEND_API_URL with your backend URL"
echo "2. ✅ Test the frontend application"
echo "3. ✅ Verify API connections are working"
echo "4. ✅ Check campaign creation and management"
echo "5. ✅ Test call initiation flow"
echo ""
echo "🔧 Configuration:"
echo "   Backend API URL: $REACT_APP_BACKEND_API_URL"
echo "   Build files: amplify_ui/build/"
echo ""
echo "🆘 Need help? Check the README.md for troubleshooting" 