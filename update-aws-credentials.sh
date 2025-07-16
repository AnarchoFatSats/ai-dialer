#!/bin/bash

# AWS Credentials Update Helper
# This script helps update AWS credentials for deployment

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 AWS Credentials Update Helper${NC}"
echo -e "${BLUE}This will help you update AWS credentials for Lambda deployment${NC}"

# Check current status
echo -e "\n${YELLOW}1. Checking current AWS status...${NC}"
if aws sts get-caller-identity > /dev/null 2>&1; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
    echo -e "${GREEN}✅ AWS credentials are working (Account: $ACCOUNT_ID)${NC}"
    echo -e "${BLUE}You can run: ./deploy-lambda.sh${NC}"
    exit 0
else
    echo -e "${RED}❌ AWS credentials are invalid or expired${NC}"
fi

# Provide options
echo -e "\n${YELLOW}2. Choose credential update method:${NC}"
echo -e "${BLUE}Option A: Use AWS CLI configure${NC}"
echo -e "  Run: aws configure"
echo -e "  Enter your AWS Access Key ID and Secret Access Key"

echo -e "\n${BLUE}Option B: Use environment variables${NC}"
echo -e "  export AWS_ACCESS_KEY_ID='your-access-key'"
echo -e "  export AWS_SECRET_ACCESS_KEY='your-secret-key'"
echo -e "  export AWS_DEFAULT_REGION='us-east-1'"

echo -e "\n${YELLOW}3. Where to get AWS credentials:${NC}"
echo -e "${BLUE}• AWS Console > IAM > Users > Security Credentials${NC}"
echo -e "${BLUE}• Or ask your AWS administrator${NC}"

echo -e "\n${YELLOW}4. After updating credentials, run:${NC}"
echo -e "${GREEN}./deploy-lambda.sh${NC}"

echo -e "\n${BLUE}💡 Need help? Check AWS-DEPLOYMENT-GUIDE.md${NC}" 