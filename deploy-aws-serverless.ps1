# AI Dialer AWS Serverless Deployment Script
# Deploy FastAPI to AWS Lambda + API Gateway (No Docker needed)

param(
    [string]$Step = "all",
    [string]$Region = "us-east-1",
    [string]$Password = "YourSecurePassword123!"
)

Write-Host "🚀 AI Dialer AWS Serverless Deployment" -ForegroundColor Green
Write-Host "Using AWS Lambda + API Gateway (No Docker!)" -ForegroundColor Yellow

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

# Step 2: Create RDS Database (Same as before)
if ($Step -eq "all" -or $Step -eq "2") {
    Write-Host "`n📋 Step 2: Creating RDS Database..." -ForegroundColor Cyan
    
    # Get default VPC
    $vpcId = aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text
    $subnets = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpcId" --query 'Subnets[*].SubnetId' --output text
    $subnetArray = $subnets -split "\s+"
    
    # Create security group for RDS
    try {
        $rdsSgId = aws ec2 create-security-group --group-name aidialer-rds-sg --description "Security group for AI Dialer RDS database" --vpc-id $vpcId --query 'GroupId' --output text
        Write-Host "✅ Created RDS Security Group: $rdsSgId" -ForegroundColor Green
    }
    catch {
        $rdsSgId = aws ec2 describe-security-groups --group-names aidialer-rds-sg --query 'SecurityGroups[0].GroupId' --output text
    }
    
    # Allow Lambda to access RDS (Lambda uses NAT Gateway, so allow from VPC)
    aws ec2 authorize-security-group-ingress --group-id $rdsSgId --protocol tcp --port 5432 --cidr 10.0.0.0/8 2>$null
    
    # Create DB subnet group
    try {
        aws rds create-db-subnet-group --db-subnet-group-name aidialer-db-subnet-group --db-subnet-group-description "Subnet group for AI Dialer database" --subnet-ids $subnetArray[0] $subnetArray[1] 2>$null
        Write-Host "✅ Created DB subnet group" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ DB subnet group already exists" -ForegroundColor Yellow
    }
    
    # Create RDS instance
    try {
        aws rds create-db-instance --db-instance-identifier aidialer-db --db-instance-class db.t3.micro --engine postgres --engine-version 15.4 --master-username postgres --master-user-password $Password --allocated-storage 20 --storage-type gp2 --storage-encrypted --db-name aidialer --vpc-security-group-ids $rdsSgId --db-subnet-group-name aidialer-db-subnet-group --backup-retention-period 7 --multi-az false --publicly-accessible false
        Write-Host "✅ RDS instance creation initiated (5-10 minutes)" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ RDS instance already exists" -ForegroundColor Yellow
    }
}

# Step 3: Create ElastiCache Redis (Same as before)
if ($Step -eq "all" -or $Step -eq "3") {
    Write-Host "`n📋 Step 3: Creating ElastiCache Redis..." -ForegroundColor Cyan
    
    # Create security group for Redis
    try {
        $redisSgId = aws ec2 create-security-group --group-name aidialer-redis-sg --description "Security group for AI Dialer Redis cache" --vpc-id $vpcId --query 'GroupId' --output text
        Write-Host "✅ Created Redis Security Group: $redisSgId" -ForegroundColor Green
    }
    catch {
        $redisSgId = aws ec2 describe-security-groups --group-names aidialer-redis-sg --query 'SecurityGroups[0].GroupId' --output text
    }
    
    # Allow Lambda to access Redis
    aws ec2 authorize-security-group-ingress --group-id $redisSgId --protocol tcp --port 6379 --cidr 10.0.0.0/8 2>$null
    
    # Create cache subnet group
    try {
        aws elasticache create-cache-subnet-group --cache-subnet-group-name aidialer-cache-subnet-group --cache-subnet-group-description "Subnet group for AI Dialer cache" --subnet-ids $subnetArray[0] $subnetArray[1] 2>$null
        Write-Host "✅ Created cache subnet group" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Cache subnet group already exists" -ForegroundColor Yellow
    }
    
    # Create Redis cluster
    try {
        aws elasticache create-cache-cluster --cache-cluster-id aidialer-redis --cache-node-type cache.t3.micro --engine redis --num-cache-nodes 1 --cache-subnet-group-name aidialer-cache-subnet-group --security-group-ids $redisSgId
        Write-Host "✅ Redis cluster creation initiated" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Redis cluster already exists" -ForegroundColor Yellow
    }
}

# Step 4: Package and Deploy Lambda Function
if ($Step -eq "all" -or $Step -eq "4") {
    Write-Host "`n📋 Step 4: Packaging Lambda Function..." -ForegroundColor Cyan
    
    # Create deployment package
    if (Test-Path "lambda-deployment.zip") {
        Remove-Item "lambda-deployment.zip"
    }
    
    # Create lambda handler
    Write-Host "Creating Lambda handler..." -ForegroundColor White
    
    # Package the application
    pip install -r requirements.txt -t ./lambda-package/ 2>$null
    Copy-Item -Path "app/*" -Destination "./lambda-package/" -Recurse -Force
    
    # Create deployment zip
    Compress-Archive -Path "./lambda-package/*" -DestinationPath "lambda-deployment.zip"
    Write-Host "✅ Lambda package created" -ForegroundColor Green
}

# Step 5: Create IAM Role for Lambda
if ($Step -eq "all" -or $Step -eq "5") {
    Write-Host "`n📋 Step 5: Creating IAM Role for Lambda..." -ForegroundColor Cyan
    
    # Create trust policy for Lambda
    $trustPolicy = @{
        Version = "2012-10-17"
        Statement = @(
            @{
                Effect = "Allow"
                Principal = @{
                    Service = "lambda.amazonaws.com"
                }
                Action = "sts:AssumeRole"
            }
        )
    } | ConvertTo-Json -Depth 10
    
    $trustPolicy | Out-File -FilePath "lambda-trust-policy.json" -Encoding utf8
    
    # Create IAM role
    try {
        aws iam create-role --role-name aidialer-lambda-role --assume-role-policy-document file://lambda-trust-policy.json
        Write-Host "✅ Lambda IAM role created" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Lambda IAM role already exists" -ForegroundColor Yellow
    }
    
    # Attach policies
    aws iam attach-role-policy --role-name aidialer-lambda-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    aws iam attach-role-policy --role-name aidialer-lambda-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole
    
    Write-Host "✅ IAM policies attached" -ForegroundColor Green
}

# Step 6: Create Lambda Function
if ($Step -eq "all" -or $Step -eq "6") {
    Write-Host "`n📋 Step 6: Creating Lambda Function..." -ForegroundColor Cyan
    
    # Wait for IAM role to be ready
    Start-Sleep -Seconds 10
    
    try {
        aws lambda create-function --function-name aidialer-api --runtime python3.9 --role arn:aws:iam::$accountId:role/aidialer-lambda-role --handler lambda_handler.handler --zip-file fileb://lambda-deployment.zip --timeout 30 --memory-size 512 --vpc-config SubnetIds=$($subnetArray[0]),$($subnetArray[1]),SecurityGroupIds=$rdsSgId,$redisSgId
        Write-Host "✅ Lambda function created" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ Lambda function already exists, updating..." -ForegroundColor Yellow
        aws lambda update-function-code --function-name aidialer-api --zip-file fileb://lambda-deployment.zip
    }
}

# Step 7: Create API Gateway
if ($Step -eq "all" -or $Step -eq "7") {
    Write-Host "`n📋 Step 7: Creating API Gateway..." -ForegroundColor Cyan
    
    try {
        $apiId = aws apigateway create-rest-api --name aidialer-api --description "AI Dialer API" --query 'id' --output text
        Write-Host "✅ API Gateway created: $apiId" -ForegroundColor Green
        
        # Get root resource
        $rootResourceId = aws apigateway get-resources --rest-api-id $apiId --query 'items[0].id' --output text
        
        # Create proxy resource
        $proxyResourceId = aws apigateway create-resource --rest-api-id $apiId --parent-id $rootResourceId --path-part '{proxy+}' --query 'id' --output text
        
        # Create method
        aws apigateway put-method --rest-api-id $apiId --resource-id $proxyResourceId --http-method ANY --authorization-type NONE
        
        # Create integration
        aws apigateway put-integration --rest-api-id $apiId --resource-id $proxyResourceId --http-method ANY --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:${Region}:lambda:path/2015-03-31/functions/arn:aws:lambda:${Region}:${accountId}:function:aidialer-api/invocations"
        
        # Add permission for API Gateway to invoke Lambda
        aws lambda add-permission --function-name aidialer-api --statement-id api-gateway-invoke --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:${Region}:${accountId}:${apiId}/*/*"
        
        # Deploy API
        aws apigateway create-deployment --rest-api-id $apiId --stage-name prod
        
        Write-Host "✅ API Gateway deployed" -ForegroundColor Green
        Write-Host "🌐 API URL: https://$apiId.execute-api.$Region.amazonaws.com/prod" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️ API Gateway setup failed" -ForegroundColor Red
    }
}

Write-Host "`n🎉 Serverless deployment complete!" -ForegroundColor Green
Write-Host "🌐 Your API is available at: https://${apiId}.execute-api.${Region}.amazonaws.com/prod" -ForegroundColor Green
Write-Host "📖 API Documentation: https://${apiId}.execute-api.${Region}.amazonaws.com/prod/docs" -ForegroundColor Green

# Cleanup
Remove-Item "lambda-trust-policy.json" -ErrorAction SilentlyContinue
Remove-Item "lambda-deployment.zip" -ErrorAction SilentlyContinue
Remove-Item "lambda-package" -Recurse -ErrorAction SilentlyContinue 