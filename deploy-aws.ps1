# AI Dialer AWS Deployment Script
# Run this script step by step to deploy the AI Dialer to AWS

param(
    [string]$Step = "all",
    [string]$Region = "us-east-1",
    [string]$Password = "YourSecurePassword123!"
)

Write-Host "🚀 AI Dialer AWS Deployment Script" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Yellow

# Step 1: Verify AWS Access
if ($Step -eq "all" -or $Step -eq "1") {
    Write-Host "`n📋 Step 1: Verifying AWS Access..." -ForegroundColor Cyan
    
    try {
        $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
        Write-Host "✅ AWS Access verified. Account: $($identity.Account)" -ForegroundColor Green
        $accountId = $identity.Account
    }
    catch {
        Write-Host "❌ AWS access failed. Please run: aws configure" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Get Default VPC
if ($Step -eq "all" -or $Step -eq "2") {
    Write-Host "`n📋 Step 2: Getting Default VPC..." -ForegroundColor Cyan
    
    $vpcId = aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text
    Write-Host "✅ Using VPC: $vpcId" -ForegroundColor Green
    
    # Get subnets
    $subnets = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpcId" --query 'Subnets[*].SubnetId' --output text
    $subnetArray = $subnets -split "\s+"
    Write-Host "✅ Found subnets: $($subnetArray -join ', ')" -ForegroundColor Green
}

# Step 3: Create Security Groups
if ($Step -eq "all" -or $Step -eq "3") {
    Write-Host "`n📋 Step 3: Creating Security Groups..." -ForegroundColor Cyan
    
    # RDS Security Group
    try {
        $rdsSgId = aws ec2 create-security-group --group-name aidialer-rds-sg --description "Security group for AI Dialer RDS database" --vpc-id $vpcId --query 'GroupId' --output text
        Write-Host "✅ Created RDS Security Group: $rdsSgId" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ RDS Security Group might already exist" -ForegroundColor Yellow
        $rdsSgId = aws ec2 describe-security-groups --group-names aidialer-rds-sg --query 'SecurityGroups[0].GroupId' --output text
    }
    
    # Redis Security Group
    try {
        $redisSgId = aws ec2 create-security-group --group-name aidialer-redis-sg --description "Security group for AI Dialer Redis cache" --vpc-id $vpcId --query 'GroupId' --output text
        Write-Host "✅ Created Redis Security Group: $redisSgId" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Redis Security Group might already exist" -ForegroundColor Yellow
        $redisSgId = aws ec2 describe-security-groups --group-names aidialer-redis-sg --query 'SecurityGroups[0].GroupId' --output text
    }
    
    # ECS Security Group
    try {
        $ecsSgId = aws ec2 create-security-group --group-name aidialer-ecs-sg --description "Security group for AI Dialer ECS tasks" --vpc-id $vpcId --query 'GroupId' --output text
        Write-Host "✅ Created ECS Security Group: $ecsSgId" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ ECS Security Group might already exist" -ForegroundColor Yellow
        $ecsSgId = aws ec2 describe-security-groups --group-names aidialer-ecs-sg --query 'SecurityGroups[0].GroupId' --output text
    }
    
    # ALB Security Group
    try {
        $albSgId = aws ec2 create-security-group --group-name aidialer-alb-sg --description "Security group for AI Dialer Application Load Balancer" --vpc-id $vpcId --query 'GroupId' --output text
        Write-Host "✅ Created ALB Security Group: $albSgId" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ ALB Security Group might already exist" -ForegroundColor Yellow
        $albSgId = aws ec2 describe-security-groups --group-names aidialer-alb-sg --query 'SecurityGroups[0].GroupId' --output text
    }
}

# Step 4: Configure Security Group Rules
if ($Step -eq "all" -or $Step -eq "4") {
    Write-Host "`n📋 Step 4: Configuring Security Group Rules..." -ForegroundColor Cyan
    
    # Allow ECS to access RDS
    aws ec2 authorize-security-group-ingress --group-id $rdsSgId --protocol tcp --port 5432 --source-group $ecsSgId 2>$null
    Write-Host "✅ Configured RDS access from ECS" -ForegroundColor Green
    
    # Allow ECS to access Redis
    aws ec2 authorize-security-group-ingress --group-id $redisSgId --protocol tcp --port 6379 --source-group $ecsSgId 2>$null
    Write-Host "✅ Configured Redis access from ECS" -ForegroundColor Green
    
    # Allow ALB to access ECS
    aws ec2 authorize-security-group-ingress --group-id $ecsSgId --protocol tcp --port 8000 --source-group $albSgId 2>$null
    Write-Host "✅ Configured ECS access from ALB" -ForegroundColor Green
    
    # Allow internet to access ALB
    aws ec2 authorize-security-group-ingress --group-id $albSgId --protocol tcp --port 80 --cidr 0.0.0.0/0 2>$null
    aws ec2 authorize-security-group-ingress --group-id $albSgId --protocol tcp --port 443 --cidr 0.0.0.0/0 2>$null
    Write-Host "✅ Configured ALB internet access" -ForegroundColor Green
}

# Step 5: Create RDS Database
if ($Step -eq "all" -or $Step -eq "5") {
    Write-Host "`n📋 Step 5: Creating RDS Database..." -ForegroundColor Cyan
    
    # Create DB subnet group
    try {
        aws rds create-db-subnet-group --db-subnet-group-name aidialer-db-subnet-group --db-subnet-group-description "Subnet group for AI Dialer database" --subnet-ids $subnetArray[0] $subnetArray[1] 2>$null
        Write-Host "✅ Created DB subnet group" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ DB subnet group might already exist" -ForegroundColor Yellow
    }
    
    # Create RDS instance
    try {
        aws rds create-db-instance --db-instance-identifier aidialer-db --db-instance-class db.t3.micro --engine postgres --engine-version 15.4 --master-username postgres --master-user-password $Password --allocated-storage 20 --storage-type gp2 --storage-encrypted --db-name aidialer --vpc-security-group-ids $rdsSgId --db-subnet-group-name aidialer-db-subnet-group --backup-retention-period 7 --multi-az false --publicly-accessible false
        Write-Host "✅ RDS instance creation initiated (this takes 5-10 minutes)" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ RDS instance might already exist" -ForegroundColor Yellow
    }
}

# Step 6: Create ElastiCache Redis
if ($Step -eq "all" -or $Step -eq "6") {
    Write-Host "`n📋 Step 6: Creating ElastiCache Redis..." -ForegroundColor Cyan
    
    # Create cache subnet group
    try {
        aws elasticache create-cache-subnet-group --cache-subnet-group-name aidialer-cache-subnet-group --cache-subnet-group-description "Subnet group for AI Dialer cache" --subnet-ids $subnetArray[0] $subnetArray[1] 2>$null
        Write-Host "✅ Created cache subnet group" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Cache subnet group might already exist" -ForegroundColor Yellow
    }
    
    # Create Redis cluster
    try {
        aws elasticache create-cache-cluster --cache-cluster-id aidialer-redis --cache-node-type cache.t3.micro --engine redis --num-cache-nodes 1 --cache-subnet-group-name aidialer-cache-subnet-group --security-group-ids $redisSgId
        Write-Host "✅ Redis cluster creation initiated" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Redis cluster might already exist" -ForegroundColor Yellow
    }
}

# Step 7: Create ECR Repository
if ($Step -eq "all" -or $Step -eq "7") {
    Write-Host "`n📋 Step 7: Creating ECR Repository..." -ForegroundColor Cyan
    
    try {
        aws ecr create-repository --repository-name aidialer --region $Region
        Write-Host "✅ ECR repository created" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ ECR repository might already exist" -ForegroundColor Yellow
    }
}

# Step 8: Create ECS Cluster
if ($Step -eq "all" -or $Step -eq "8") {
    Write-Host "`n📋 Step 8: Creating ECS Cluster..." -ForegroundColor Cyan
    
    try {
        aws ecs create-cluster --cluster-name aidialer-cluster --capacity-providers FARGATE --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1
        Write-Host "✅ ECS cluster created" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ ECS cluster might already exist" -ForegroundColor Yellow
    }
}

Write-Host "`n🎉 Infrastructure setup complete!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Wait for RDS and Redis to be available (5-10 minutes)" -ForegroundColor White
Write-Host "2. Install Docker Desktop for Windows" -ForegroundColor White
Write-Host "3. Build and push Docker image to ECR" -ForegroundColor White
Write-Host "4. Create and deploy ECS service" -ForegroundColor White

# Output important values
Write-Host "`n📝 Important Values:" -ForegroundColor Cyan
Write-Host "Account ID: $accountId" -ForegroundColor White
Write-Host "VPC ID: $vpcId" -ForegroundColor White
Write-Host "RDS Security Group: $rdsSgId" -ForegroundColor White
Write-Host "Redis Security Group: $redisSgId" -ForegroundColor White
Write-Host "ECS Security Group: $ecsSgId" -ForegroundColor White
Write-Host "ALB Security Group: $albSgId" -ForegroundColor White 