#!/bin/bash
# AI Voice Dialer - AWS Deployment Script
# This script automates the deployment of the AI voice dialer to AWS ECS Fargate

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="ai-voice-dialer"
AWS_REGION="us-east-1"
ENVIRONMENT="production"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    print_status "Checking requirements..."
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install it first:"
        echo "curl 'https://awscli.amazonaws.com/AWSCLIV2.pkg' -o 'AWSCLIV2.pkg'"
        echo "sudo installer -pkg AWSCLIV2.pkg -target /"
        exit 1
    fi
    
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform not found. Please install it first:"
        echo "brew install terraform"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install it first:"
        echo "brew install docker"
        exit 1
    fi
    
    print_success "All requirements satisfied"
}

# Check AWS credentials
check_aws_credentials() {
    print_status "Checking AWS credentials..."
    
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run:"
        echo "aws configure"
        exit 1
    fi
    
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_success "AWS credentials valid (Account: $AWS_ACCOUNT_ID)"
}

# Build and push Docker image
build_and_push_image() {
    print_status "Building and pushing Docker image..."
    
    # Get ECR repository URL
    ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}"
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO
    
    # Build image
    docker build -t $APP_NAME .
    
    # Tag image
    docker tag $APP_NAME:latest $ECR_REPO:latest
    
    # Push image
    docker push $ECR_REPO:latest
    
    print_success "Docker image pushed to ECR"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    print_status "Deploying infrastructure with Terraform..."
    
    # Initialize Terraform
    terraform init
    
    # Plan deployment
    terraform plan \
        -var="aws_region=$AWS_REGION" \
        -var="environment=$ENVIRONMENT" \
        -var="app_name=$APP_NAME" \
        -out=tfplan
    
    # Apply deployment
    terraform apply tfplan
    
    print_success "Infrastructure deployed successfully"
}

# Update ECS service
update_ecs_service() {
    print_status "Updating ECS service..."
    
    # Force new deployment
    aws ecs update-service \
        --cluster "${APP_NAME}-cluster" \
        --service $APP_NAME \
        --force-new-deployment \
        --region $AWS_REGION
    
    print_success "ECS service updated"
}

# Wait for deployment to complete
wait_for_deployment() {
    print_status "Waiting for deployment to complete..."
    
    aws ecs wait services-stable \
        --cluster "${APP_NAME}-cluster" \
        --services $APP_NAME \
        --region $AWS_REGION
    
    print_success "Deployment completed successfully"
}

# Get deployment info
get_deployment_info() {
    print_status "Getting deployment information..."
    
    # Get load balancer DNS
    ALB_DNS=$(terraform output -raw load_balancer_dns)
    
    # Get database endpoint
    DB_ENDPOINT=$(terraform output -raw database_endpoint)
    
    # Get Redis endpoint
    REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)
    
    # Get ECR repository URL
    ECR_URL=$(terraform output -raw ecr_repository_url)
    
    # Get S3 bucket name
    S3_BUCKET=$(terraform output -raw s3_bucket_name)
    
    echo ""
    echo "======================================="
    echo "🚀 AI Voice Dialer Deployment Complete!"
    echo "======================================="
    echo ""
    echo "📊 Application URL: http://$ALB_DNS"
    echo "📚 API Documentation: http://$ALB_DNS/docs"
    echo "🔍 Health Check: http://$ALB_DNS/health"
    echo ""
    echo "🏢 Infrastructure Details:"
    echo "  • Load Balancer DNS: $ALB_DNS"
    echo "  • Database Endpoint: $DB_ENDPOINT"
    echo "  • Redis Endpoint: $REDIS_ENDPOINT"
    echo "  • ECR Repository: $ECR_URL"
    echo "  • S3 Bucket: $S3_BUCKET"
    echo ""
    echo "📈 Monitoring:"
    echo "  • CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#logsV2:log-groups"
    echo "  • ECS Console: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters"
    echo ""
    echo "🔧 Next Steps:"
    echo "1. Update your DNS to point to: $ALB_DNS"
    echo "2. Configure SSL certificate for HTTPS"
    echo "3. Set up your AI service API keys in ECS environment variables"
    echo "4. Create your first campaign and start dialing!"
    echo ""
}

# Main deployment function
main() {
    echo ""
    echo "🤖📞 AI Voice Dialer - AWS Deployment"
    echo "======================================"
    echo ""
    
    # Check if this is a first-time deployment
    if [ "$1" = "--first-time" ]; then
        print_status "First-time deployment detected"
        
        check_requirements
        check_aws_credentials
        deploy_infrastructure
        
        # Wait a moment for ECR repository to be created
        sleep 30
        
        build_and_push_image
        update_ecs_service
        wait_for_deployment
        get_deployment_info
        
    elif [ "$1" = "--update" ]; then
        print_status "Application update deployment"
        
        check_requirements
        check_aws_credentials
        build_and_push_image
        update_ecs_service
        wait_for_deployment
        
        print_success "Application updated successfully"
        
    else
        echo "Usage:"
        echo "  $0 --first-time    Deploy infrastructure and application"
        echo "  $0 --update        Update application only"
        echo ""
        echo "Examples:"
        echo "  $0 --first-time    # First deployment"
        echo "  $0 --update        # Update after code changes"
        echo ""
        exit 1
    fi
}

# Run main function
main "$@" 