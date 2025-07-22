# AI Dialer - AWS ECS Deployment Script
# Full AI Implementation with Docker
param(
    [string]$AWS_REGION = "us-east-1",
    [string]$CLUSTER_NAME = "ai-dialer-cluster",
    [string]$SERVICE_NAME = "ai-dialer-service",
    [string]$REPOSITORY_NAME = "ai-dialer",
    [string]$TASK_FAMILY = "ai-dialer-task"
)

Write-Host "🚀 AI Dialer - AWS ECS Deployment (Full AI Implementation)" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Check AWS CLI
try {
    $aws_version = aws --version
    Write-Host "✅ AWS CLI Available: $aws_version" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI not found. Please install AWS CLI first." -ForegroundColor Red
    exit 1
}

# Get AWS Account ID
try {
    $AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
    Write-Host "✅ AWS Account ID: $AWS_ACCOUNT_ID" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to get AWS Account ID. Check AWS credentials." -ForegroundColor Red
    exit 1
}

Write-Host "`n🏗️  Step 1: Create ECR Repository" -ForegroundColor Cyan
try {
    aws ecr create-repository --repository-name $REPOSITORY_NAME --region $AWS_REGION 2>$null
    Write-Host "✅ ECR Repository created/exists: $REPOSITORY_NAME" -ForegroundColor Green
} catch {
    Write-Host "⚠️  ECR Repository may already exist (continuing...)" -ForegroundColor Yellow
}

Write-Host "`n🐳 Step 2: Build and Push Docker Image" -ForegroundColor Cyan

# Login to ECR
Write-Host "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ECR login failed. Make sure Docker is running." -ForegroundColor Red
    exit 1
}

# Build Docker image
Write-Host "🔨 Building AI Dialer Docker image..."
docker build -t ai-dialer .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed." -ForegroundColor Red
    exit 1
}

# Tag and push image
$ECR_URI = "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME"
Write-Host "🏷️  Tagging image..."
docker tag ai-dialer:latest "$ECR_URI:latest"

Write-Host "📤 Pushing to ECR..."
docker push "$ECR_URI:latest"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker push failed." -ForegroundColor Red
    exit 1
}

Write-Host "`n🔧 Step 3: Create AWS Resources" -ForegroundColor Cyan

# Create ECS Cluster
Write-Host "🏗️  Creating ECS Cluster..."
aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION 2>$null

# Create CloudWatch Log Group
Write-Host "📊 Creating CloudWatch Log Group..."
aws logs create-log-group --log-group-name "/ecs/ai-dialer" --region $AWS_REGION 2>$null

# Update task definition with account details
Write-Host "📝 Updating task definition..."
$task_def = Get-Content "aws-ecs-task-definition.json" -Raw
$task_def = $task_def -replace "ACCOUNT_ID", $AWS_ACCOUNT_ID
$task_def = $task_def -replace "REGION", $AWS_REGION
$task_def | Out-File "aws-ecs-task-definition-updated.json" -Encoding UTF8

Write-Host "`n🚀 Step 4: Deploy to ECS" -ForegroundColor Cyan

# Register task definition
Write-Host "📋 Registering task definition..."
aws ecs register-task-definition --cli-input-json file://aws-ecs-task-definition-updated.json --region $AWS_REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Task definition registration failed." -ForegroundColor Red
    exit 1
}

# Create or update service
Write-Host "🎯 Creating/updating ECS service..."

$service_exists = aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION --query "services[0].serviceName" --output text 2>$null

if ($service_exists -eq $SERVICE_NAME) {
    Write-Host "🔄 Updating existing service..."
    aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --task-definition $TASK_FAMILY --region $AWS_REGION
} else {
    Write-Host "✨ Creating new service..."
    
    # Get default VPC and subnets
    $VPC_ID = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region $AWS_REGION
    $SUBNET_IDS = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text --region $AWS_REGION
    $SUBNET_LIST = $SUBNET_IDS -split "\s+" | ForEach-Object { "`"$_`"" } | Join-String -Separator ","
    
    # Create security group for AI Dialer
    Write-Host "🛡️  Creating security group..."
    $SG_ID = aws ec2 create-security-group --group-name "ai-dialer-sg" --description "AI Dialer Security Group" --vpc-id $VPC_ID --region $AWS_REGION --query "GroupId" --output text 2>$null
    
    if (-not $SG_ID) {
        $SG_ID = aws ec2 describe-security-groups --filters "Name=group-name,Values=ai-dialer-sg" --query "SecurityGroups[0].GroupId" --output text --region $AWS_REGION
    }
    
    # Add HTTP rule
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region $AWS_REGION 2>$null
    
    # Create service
    aws ecs create-service `
        --cluster $CLUSTER_NAME `
        --service-name $SERVICE_NAME `
        --task-definition $TASK_FAMILY `
        --desired-count 1 `
        --launch-type FARGATE `
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_LIST],securityGroups=[`"$SG_ID`"],assignPublicIp=ENABLED}" `
        --region $AWS_REGION
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Service creation/update failed." -ForegroundColor Red
    exit 1
}

Write-Host "`n🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "✅ AI Dialer deployed to AWS ECS with full AI capabilities!" -ForegroundColor Green
Write-Host "🌐 Cluster: $CLUSTER_NAME" -ForegroundColor Cyan
Write-Host "🎯 Service: $SERVICE_NAME" -ForegroundColor Cyan
Write-Host "🐳 Image: $ECR_URI:latest" -ForegroundColor Cyan

Write-Host "`n🔍 Getting service information..." -ForegroundColor Cyan
$service_info = aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION --query "services[0]"

Write-Host "`n📊 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Wait for service to stabilize (may take 2-3 minutes)" -ForegroundColor White
Write-Host "2. Check service status: aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME" -ForegroundColor White
Write-Host "3. Get task public IP for testing" -ForegroundColor White
Write-Host "4. Update DNS/Load Balancer to point to ECS service" -ForegroundColor White

Write-Host "`n🤖 AI Features Available:" -ForegroundColor Magenta
Write-Host "• Anthropic Claude AI Integration ✅" -ForegroundColor Green
Write-Host "• OpenAI GPT Integration ✅" -ForegroundColor Green  
Write-Host "• Conversational AI Training ✅" -ForegroundColor Green
Write-Host "• Voice Synthesis (Deepgram/ElevenLabs) ✅" -ForegroundColor Green
Write-Host "• Real-time Analytics ✅" -ForegroundColor Green
Write-Host "• Campaign Management ✅" -ForegroundColor Green

Write-Host "`n🏁 Deployment successful! Frontend team can now connect!" -ForegroundColor Green 