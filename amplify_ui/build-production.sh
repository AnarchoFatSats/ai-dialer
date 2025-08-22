#!/bin/bash
# AI Dialer Frontend - Production Build Script
# Prepares the application for production deployment

echo "🚀 AI Dialer - Production Build Starting..."
echo "================================================"

# Set production environment variables
export NODE_ENV=production
export REACT_APP_ENVIRONMENT=production
export REACT_APP_BACKEND_API_URL=http://ai-dialer-alb-959576006.us-east-1.elb.amazonaws.com
export REACT_APP_WS_BASE_URL=ws://ai-dialer-alb-959576006.us-east-1.elb.amazonaws.com
export REACT_APP_ENABLE_REAL_TIME_UPDATES=true
export REACT_APP_ENABLE_NOTIFICATIONS=true
export REACT_APP_ENABLE_ANALYTICS=true
export REACT_APP_DEBUG_MODE=false
export REACT_APP_USE_MOCK_DATA=false
export GENERATE_SOURCEMAP=false
export INLINE_RUNTIME_CHUNK=false

echo "✅ Environment Variables Set:"
echo "   - NODE_ENV: $NODE_ENV"
echo "   - Backend URL: $REACT_APP_BACKEND_API_URL"
echo "   - Debug Mode: $REACT_APP_DEBUG_MODE"
echo ""

# Check if current backend is accessible
echo "🔍 Checking backend connectivity..."
if curl -s --connect-timeout 5 "$REACT_APP_BACKEND_API_URL/health" > /dev/null; then
    echo "✅ Backend is accessible at $REACT_APP_BACKEND_API_URL"
else
    echo "⚠️  Warning: Backend may not be accessible"
    echo "   Run: ../update-backend-url.sh to get latest IP"
fi
echo ""

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf build/
echo "✅ Build directory cleaned"
echo ""

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm ci
    echo "✅ Dependencies installed"
    echo ""
fi

# Build for production
echo "🔨 Building for production..."
npm run build

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Production Build Successful!"
    echo "================================================"
    echo "✅ Build artifacts created in: ./build/"
    echo "✅ Ready for Amplify deployment"
    echo "✅ Backend configured: $REACT_APP_BACKEND_API_URL"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Deploy to Amplify: git push origin main"
    echo "   2. Update CORS in backend for your domain"
    echo "   3. Monitor deployment in Amplify console"
    echo ""
    echo "🔗 Build size analysis:"
    du -sh build/
    echo ""
else
    echo ""
    echo "❌ Production Build Failed!"
    echo "Check the errors above and fix them before deployment"
    exit 1
fi 