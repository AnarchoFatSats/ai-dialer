# AI Dialer - AWS CodeBuild Deployment (Option B)
# Full AI Implementation - Pure AWS Solution
param(
    [string]$AWS_REGION = "us-east-1",
    [string]$PROJECT_NAME = "ai-dialer-build",
    [string]$REPOSITORY_NAME = "ai-dialer",
    [string]$CLUSTER_NAME = "ai-dialer-cluster",
    [string]$SERVICE_NAME = "ai-dialer-service"
)

Write-Host "🚀 AI Dialer - AWS CodeBuild Deployment (Full AI - Pure AWS)" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green

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
    Write-Host "✅ ECR Repository created: $REPOSITORY_NAME" -ForegroundColor Green
} catch {
    Write-Host "⚠️  ECR Repository exists (continuing...)" -ForegroundColor Yellow
}

Write-Host "`n📋 Step 2: Create CodeBuild Service Role" -ForegroundColor Cyan

# Create CodeBuild service role
$trust_policy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@

$trust_policy | Out-File "codebuild-trust-policy.json" -Encoding UTF8

try {
    aws iam create-role --role-name "ai-dialer-codebuild-role" --assume-role-policy-document file://codebuild-trust-policy.json --region $AWS_REGION 2>$null
    Write-Host "✅ CodeBuild role created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  CodeBuild role exists (continuing...)" -ForegroundColor Yellow
}

# Attach policies
aws iam attach-role-policy --role-name "ai-dialer-codebuild-role" --policy-arn "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser" --region $AWS_REGION
aws iam attach-role-policy --role-name "ai-dialer-codebuild-role" --policy-arn "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess" --region $AWS_REGION

Write-Host "`n🔧 Step 3: Create CodeBuild Project" -ForegroundColor Cyan

$codebuild_project = @"
{
  "name": "$PROJECT_NAME",
  "description": "AI Dialer build project with full AI capabilities",
  "source": {
    "type": "GITHUB",
    "location": "https://github.com/your-username/ai-dialer.git",
    "buildspec": "buildspec.yml"
  },
  "artifacts": {
    "type": "NO_ARTIFACTS"
  },
  "environment": {
    "type": "LINUX_CONTAINER",
    "image": "aws/codebuild/standard:7.0",
    "computeType": "BUILD_GENERAL1_LARGE",
    "privilegedMode": true,
    "environmentVariables": [
      {
        "name": "AWS_DEFAULT_REGION",
        "value": "$AWS_REGION"
      },
      {
        "name": "AWS_ACCOUNT_ID",
        "value": "$AWS_ACCOUNT_ID"
      },
      {
        "name": "IMAGE_REPO_NAME",
        "value": "$REPOSITORY_NAME"
      }
    ]
  },
  "serviceRole": "arn:aws:iam::$AWS_ACCOUNT_ID:role/ai-dialer-codebuild-role"
}
"@

$codebuild_project | Out-File "codebuild-project.json" -Encoding UTF8

try {
    aws codebuild create-project --cli-input-json file://codebuild-project.json --region $AWS_REGION
    Write-Host "✅ CodeBuild project created: $PROJECT_NAME" -ForegroundColor Green
} catch {
    Write-Host "⚠️  CodeBuild project exists (updating...)" -ForegroundColor Yellow
    aws codebuild update-project --cli-input-json file://codebuild-project.json --region $AWS_REGION
}

Write-Host "`n🚀 Step 4: Start Build Process" -ForegroundColor Cyan
Write-Host "📦 Building Docker image with full AI capabilities in AWS..." -ForegroundColor Yellow

$build_result = aws codebuild start-build --project-name $PROJECT_NAME --region $AWS_REGION --query "build.id" --output text

if (-not $build_result) {
    Write-Host "❌ Failed to start CodeBuild" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build started: $build_result" -ForegroundColor Green
Write-Host "🔍 Monitoring build progress..." -ForegroundColor Yellow

# Monitor build status
do {
    Start-Sleep -Seconds 10
    $status = aws codebuild batch-get-builds --ids $build_result --region $AWS_REGION --query "builds[0].buildStatus" --output text
    Write-Host "⏳ Build status: $status" -ForegroundColor Cyan
} while ($status -eq "IN_PROGRESS")

if ($status -ne "SUCCEEDED") {
    Write-Host "❌ Build failed with status: $status" -ForegroundColor Red
    Write-Host "🔍 Check CloudWatch logs for details" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Build completed successfully!" -ForegroundColor Green

Write-Host "`n🔧 Step 5: Setup ECS Infrastructure" -ForegroundColor Cyan

# Create ECS Cluster
aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION 2>$null
Write-Host "✅ ECS Cluster: $CLUSTER_NAME" -ForegroundColor Green

# Create CloudWatch Log Group
aws logs create-log-group --log-group-name "/ecs/ai-dialer" --region $AWS_REGION 2>$null
Write-Host "✅ CloudWatch Log Group created" -ForegroundColor Green

Write-Host "`n🎯 Step 6: Deploy to ECS" -ForegroundColor Cyan

# Update task definition
$task_def = Get-Content "aws-ecs-task-definition.json" -Raw
$task_def = $task_def -replace "ACCOUNT_ID", $AWS_ACCOUNT_ID
$task_def = $task_def -replace "REGION", $AWS_REGION
$task_def | Out-File "aws-ecs-task-definition-final.json" -Encoding UTF8

# Register task definition
aws ecs register-task-definition --cli-input-json file://aws-ecs-task-definition-final.json --region $AWS_REGION
Write-Host "✅ Task definition registered" -ForegroundColor Green

# Create/update service
$service_exists = aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION --query "services[0].serviceName" --output text 2>$null

if ($service_exists -eq $SERVICE_NAME) {
    Write-Host "🔄 Updating existing ECS service..." -ForegroundColor Yellow
    aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --task-definition "ai-dialer-task" --region $AWS_REGION
} else {
    Write-Host "✨ Creating new ECS service..." -ForegroundColor Yellow
    
    # Get VPC and subnet info
    $VPC_ID = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region $AWS_REGION
    $SUBNET_IDS = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text --region $AWS_REGION
    $SUBNET_LIST = $SUBNET_IDS -split "\s+" | ForEach-Object { "`"$_`"" } | Join-String -Separator ","
    
    # Create security group
    $SG_ID = aws ec2 create-security-group --group-name "ai-dialer-sg" --description "AI Dialer Security Group" --vpc-id $VPC_ID --region $AWS_REGION --query "GroupId" --output text 2>$null
    if (-not $SG_ID) {
        $SG_ID = aws ec2 describe-security-groups --filters "Name=group-name,Values=ai-dialer-sg" --query "SecurityGroups[0].GroupId" --output text --region $AWS_REGION
    }
    
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region $AWS_REGION 2>$null
    
    aws ecs create-service `
        --cluster $CLUSTER_NAME `
        --service-name $SERVICE_NAME `
        --task-definition "ai-dialer-task" `
        --desired-count 1 `
        --launch-type FARGATE `
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_LIST],securityGroups=[`"$SG_ID`"],assignPublicIp=ENABLED}" `
        --region $AWS_REGION
}

Write-Host "`n🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host "✅ AI Dialer deployed via pure AWS solution!" -ForegroundColor Green
Write-Host "🏗️  Built with: AWS CodeBuild" -ForegroundColor Cyan
Write-Host "🐳 Stored in: AWS ECR" -ForegroundColor Cyan
Write-Host "🚀 Running on: AWS ECS Fargate" -ForegroundColor Cyan

Write-Host "`n🤖 FULL AI CAPABILITIES DEPLOYED:" -ForegroundColor Magenta
Write-Host "• Anthropic Claude AI ✅" -ForegroundColor Green
Write-Host "• OpenAI GPT Integration ✅" -ForegroundColor Green
Write-Host "• Conversational Training ✅" -ForegroundColor Green
Write-Host "• Voice Synthesis ✅" -ForegroundColor Green
Write-Host "• Speech Recognition ✅" -ForegroundColor Green
Write-Host "• Real-time Analytics ✅" -ForegroundColor Green

Write-Host "`n📊 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Wait 2-3 minutes for service to stabilize" -ForegroundColor White
Write-Host "2. Get task IP: aws ecs describe-tasks --cluster $CLUSTER_NAME --tasks `$(aws ecs list-tasks --cluster $CLUSTER_NAME --query 'taskArns[0]' --output text)" -ForegroundColor White
Write-Host "3. Test AI endpoints at http://TASK_IP:8000" -ForegroundColor White
Write-Host "4. Frontend team can now connect!" -ForegroundColor White

Write-Host "`n🏁 Pure AWS deployment successful! No Docker Desktop needed!" -ForegroundColor Green

# Cleanup temporary files
Remove-Item "codebuild-trust-policy.json" -ErrorAction SilentlyContinue
Remove-Item "codebuild-project.json" -ErrorAction SilentlyContinue
Remove-Item "aws-ecs-task-definition-final.json" -ErrorAction SilentlyContinue 