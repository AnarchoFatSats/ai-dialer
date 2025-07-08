#!/bin/bash

# Elite AI Dialer - AWS Amplify Deployment Script
# This script deploys the luxury-themed UI to AWS Amplify

set -e

echo "🚀 Deploying Elite AI Dialer UI to AWS Amplify..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
GOLD='\033[1;93m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    echo "Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

echo -e "${GOLD}✨ AWS CLI configured successfully${NC}"

# Variables
APP_NAME="elite-ai-dialer"
REGION="us-east-1"
DOMAIN_NAME=""  # Optional: Set your custom domain

# Check if app exists
APP_EXISTS=$(aws amplify list-apps --region $REGION --query "apps[?name=='$APP_NAME'].appId" --output text)

if [ -z "$APP_EXISTS" ]; then
    echo -e "${YELLOW}📱 Creating new Amplify app: $APP_NAME${NC}"
    
    # Create Amplify app
    APP_ID=$(aws amplify create-app \
        --name "$APP_NAME" \
        --description "Elite AI Voice Dialer - Premium outbound calling platform" \
        --region $REGION \
        --platform "WEB" \
        --environment-variables \
            REACT_APP_API_URL="https://api.yourdomain.com",REACT_APP_WS_URL="wss://api.yourdomain.com/ws" \
        --build-spec file://amplify.yml \
        --custom-rules '[
            {
                "source": "/<*>",
                "target": "/index.html",
                "status": "404-200"
            }
        ]' \
        --tags "Environment=production,Project=ai-dialer,Tier=elite" \
        --query 'app.appId' --output text)
    
    echo -e "${GREEN}✅ Created Amplify app with ID: $APP_ID${NC}"
else
    APP_ID=$APP_EXISTS
    echo -e "${GREEN}✅ Using existing Amplify app with ID: $APP_ID${NC}"
fi

# Create Git repository URL (you'll need to replace this with your actual repo)
REPO_URL="https://github.com/yourusername/ai-dialer-ui.git"

echo -e "${YELLOW}📝 Setting up Git repository connection...${NC}"
echo -e "${YELLOW}Please manually connect your GitHub repository in the AWS Console:${NC}"
echo -e "${YELLOW}1. Go to: https://console.aws.amazon.com/amplify/home?region=$REGION#/$APP_ID${NC}"
echo -e "${YELLOW}2. Click 'Connect branch'${NC}"
echo -e "${YELLOW}3. Connect your GitHub repository${NC}"
echo -e "${YELLOW}4. Select the main/master branch${NC}"
echo -e "${YELLOW}5. Configure build settings (amplify.yml is already created)${NC}"

# Environment variables for production
echo -e "${GOLD}🔧 Setting environment variables...${NC}"

aws amplify put-app \
    --app-id $APP_ID \
    --name "$APP_NAME" \
    --environment-variables \
        REACT_APP_API_URL="https://api.yourdomain.com" \
        REACT_APP_WS_URL="wss://api.yourdomain.com/ws" \
        REACT_APP_ENVIRONMENT="production" \
        REACT_APP_VERSION="1.0.0" \
    --region $REGION

# Create production branch
echo -e "${GOLD}🌿 Setting up production branch...${NC}"

# Custom domain setup (if provided)
if [ ! -z "$DOMAIN_NAME" ]; then
    echo -e "${GOLD}🌐 Setting up custom domain: $DOMAIN_NAME${NC}"
    
    # Note: You'll need to manually verify domain ownership in AWS Console
    aws amplify create-domain-association \
        --app-id $APP_ID \
        --domain-name $DOMAIN_NAME \
        --sub-domain-settings "prefix=www,branchName=main" \
        --region $REGION
    
    echo -e "${YELLOW}⚠️  Please verify domain ownership in AWS Console${NC}"
fi

# Output useful information
echo -e "${GREEN}🎉 Deployment setup complete!${NC}"
echo -e "${GOLD}📱 App ID: $APP_ID${NC}"
echo -e "${GOLD}🌐 Amplify Console: https://console.aws.amazon.com/amplify/home?region=$REGION#/$APP_ID${NC}"
echo -e "${GOLD}🔗 Default URL: https://$APP_ID.amplifyapp.com${NC}"

echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo -e "${YELLOW}1. Connect your GitHub repository in the Amplify Console${NC}"
echo -e "${YELLOW}2. Push your code to trigger the first build${NC}"
echo -e "${YELLOW}3. Configure your API endpoints in environment variables${NC}"
echo -e "${YELLOW}4. Set up custom domain (optional)${NC}"
echo ""

echo -e "${GREEN}✨ Your Elite AI Dialer dashboard will be available shortly!${NC}"
echo -e "${GOLD}💰 Ready to generate wealth with AI-powered calling! 💰${NC}"

# Create a .env.example file for reference
cat > .env.example << EOF
# Elite AI Dialer - Environment Variables
REACT_APP_API_URL=https://your-api-domain.com
REACT_APP_WS_URL=wss://your-api-domain.com/ws
REACT_APP_ENVIRONMENT=production
REACT_APP_VERSION=1.0.0

# Optional: Analytics and tracking
REACT_APP_GOOGLE_ANALYTICS_ID=GA-XXXXXXXXX
REACT_APP_HOTJAR_ID=XXXXXXX
EOF

echo -e "${GREEN}📝 Created .env.example file for reference${NC}"

exit 0 