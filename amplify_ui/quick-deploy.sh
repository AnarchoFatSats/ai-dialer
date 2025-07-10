#!/bin/bash

# Quick Deploy to Amplify
# This script helps deploy the Elite AI Dialer UI

echo "🚀 Quick Deploy to AWS Amplify"
echo "=============================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ Node.js and npm are installed"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the project
echo "🔨 Building the project..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo ""
    echo "📝 Manual Deployment Steps:"
    echo "1. Go to: https://console.aws.amazon.com/amplify/"
    echo "2. Find your app (elite-ai-dialer)"
    echo "3. Connect your GitHub repository"
    echo "4. Set root directory to: amplify_ui"
    echo "5. The build will use the amplify.yml configuration"
    echo ""
    echo "🎯 Your app URL: https://main.dwrcfhzubtd6l.amplifyapp.com"
    echo ""
    echo "Build folder is ready at: ./build"
else
    echo "❌ Build failed. Please check the errors above."
    exit 1
fi 