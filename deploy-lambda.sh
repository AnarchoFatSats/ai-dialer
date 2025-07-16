#!/bin/bash

# AI Dialer Lambda Deployment Script
# Based on simple-deploy.ps1 but adapted for bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying AI Dialer to AWS Lambda...${NC}"

# Step 1: Verify AWS credentials
echo -e "\n${BLUE}🔐 Verifying AWS credentials...${NC}"
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS credentials are invalid or expired${NC}"
    echo -e "${YELLOW}Please run: aws configure${NC}"
    echo -e "${YELLOW}Or set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION${NC}"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
echo -e "${GREEN}✅ AWS credentials verified (Account: $ACCOUNT_ID)${NC}"

# Step 2: Check if deployment package exists
echo -e "\n${BLUE}📦 Checking deployment package...${NC}"
if [ ! -f "lambda-deployment.zip" ]; then
    echo -e "${RED}❌ lambda-deployment.zip not found${NC}"
    echo -e "${YELLOW}Please run: python3 test_lambda_locally.py to create the package${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Deployment package found${NC}"

# Step 3: Create or update Lambda function
echo -e "\n${BLUE}⚡ Updating Lambda function...${NC}"

# Check if function exists
if aws lambda get-function --function-name aidialer-api > /dev/null 2>&1; then
    echo -e "${YELLOW}📝 Updating existing Lambda function...${NC}"
    
    # Update function code
    aws lambda update-function-code \
        --function-name aidialer-api \
        --zip-file fileb://lambda-deployment.zip
    
    echo -e "${GREEN}✅ Lambda function updated${NC}"
else
    echo -e "${RED}❌ Lambda function 'aidialer-api' not found${NC}"
    echo -e "${YELLOW}Please run the full deployment script to create the function${NC}"
    exit 1
fi

# Step 4: Test the deployment
echo -e "\n${BLUE}🧪 Testing deployment...${NC}"

# Get API Gateway URL (assuming it follows the pattern)
API_URL="https://751fnxwec1.execute-api.us-east-1.amazonaws.com/prod"

# Test health endpoint
echo -e "${YELLOW}Testing health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s "$API_URL/health" | jq -r '.version // "error"')

if [ "$HEALTH_RESPONSE" = "1.0.0-production" ]; then
    echo -e "${GREEN}✅ Health check passed - Version: $HEALTH_RESPONSE${NC}"
else
    echo -e "${RED}❌ Health check failed - Response: $HEALTH_RESPONSE${NC}"
fi

# Test conversational training endpoint
echo -e "${YELLOW}Testing conversational training...${NC}"
TRAINING_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d '{"user_id": "test"}' "$API_URL/conversational-training/start" | jq -r '.message // "error"')

if [[ "$TRAINING_RESPONSE" == *"Reach"* ]]; then
    echo -e "${GREEN}✅ Conversational training working - Reach guide active${NC}"
else
    echo -e "${RED}❌ Conversational training failed - Response: $TRAINING_RESPONSE${NC}"
fi

# Final success message
echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${BLUE}🌐 API URL: $API_URL${NC}"
echo -e "${BLUE}❤️ Health Check: $API_URL/health${NC}"
echo -e "${BLUE}🤖 AI Training: $API_URL/conversational-training/start${NC}"

echo -e "\n${GREEN}✅ The frontend at https://main.dwrcfhzub1d6l.amplifyapp.com should now work with the enhanced backend!${NC}" 