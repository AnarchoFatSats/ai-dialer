# Simple AI Dialer Lambda Deployment
Write-Host "🚀 Deploying AI Dialer to AWS Lambda..." -ForegroundColor Green

# Step 1: Create Lambda deployment package
Write-Host "`n📦 Creating deployment package..." -ForegroundColor Cyan

# Clean up previous packages
if (Test-Path "lambda-package") { Remove-Item "lambda-package" -Recurse -Force }
if (Test-Path "lambda-deployment.zip") { Remove-Item "lambda-deployment.zip" -Force }

# Create package directory
New-Item -ItemType Directory -Path "lambda-package" -Force | Out-Null

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor White
pip install -r requirements.txt -t ./lambda-package/ --quiet

# Copy application code
Write-Host "Copying application code..." -ForegroundColor White
Copy-Item -Path "app" -Destination "./lambda-package/" -Recurse -Force
Copy-Item -Path "lambda_handler.py" -Destination "./lambda-package/" -Force

# Create ZIP file
Write-Host "Creating deployment ZIP..." -ForegroundColor White
Compress-Archive -Path "./lambda-package/*" -DestinationPath "lambda-deployment.zip" -Force

Write-Host "✅ Deployment package created" -ForegroundColor Green

# Step 2: Create IAM role for Lambda
Write-Host "`n🔐 Creating IAM role..." -ForegroundColor Cyan

$trustPolicy = @'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
'@

$trustPolicy | Out-File -FilePath "lambda-trust-policy.json" -Encoding utf8

# Create role
aws iam create-role --role-name aidialer-lambda-role --assume-role-policy-document file://lambda-trust-policy.json 2>$null
aws iam attach-role-policy --role-name aidialer-lambda-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

Write-Host "✅ IAM role configured" -ForegroundColor Green

# Step 3: Create Lambda function
Write-Host "`n⚡ Creating Lambda function..." -ForegroundColor Cyan

# Wait for role to be ready
Start-Sleep -Seconds 10

# Get account ID
$accountId = (aws sts get-caller-identity --query 'Account' --output text)

# Create or update Lambda function
$lambdaExists = aws lambda get-function --function-name aidialer-api 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Updating existing Lambda function..." -ForegroundColor Yellow
    aws lambda update-function-code --function-name aidialer-api --zip-file fileb://lambda-deployment.zip
} else {
    Write-Host "Creating new Lambda function..." -ForegroundColor White
    aws lambda create-function `
        --function-name aidialer-api `
        --runtime python3.9 `
        --role "arn:aws:iam::$accountId:role/aidialer-lambda-role" `
        --handler lambda_handler.lambda_handler `
        --zip-file fileb://lambda-deployment.zip `
        --timeout 30 `
        --memory-size 512 `
        --environment Variables='{ENVIRONMENT=production,DEBUG=false}'
}

Write-Host "✅ Lambda function deployed" -ForegroundColor Green

# Step 4: Create API Gateway
Write-Host "`n🌐 Creating API Gateway..." -ForegroundColor Cyan

# Create REST API
$apiId = aws apigateway create-rest-api --name aidialer-api --description "AI Dialer API" --query 'id' --output text

if ($apiId) {
    Write-Host "API Gateway created: $apiId" -ForegroundColor White
    
    # Get root resource
    $rootResourceId = aws apigateway get-resources --rest-api-id $apiId --query 'items[0].id' --output text
    
    # Create proxy resource
    $proxyResourceId = aws apigateway create-resource --rest-api-id $apiId --parent-id $rootResourceId --path-part '{proxy+}' --query 'id' --output text
    
    # Create method
    aws apigateway put-method --rest-api-id $apiId --resource-id $proxyResourceId --http-method ANY --authorization-type NONE
    
    # Create integration
    aws apigateway put-integration --rest-api-id $apiId --resource-id $proxyResourceId --http-method ANY --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:$accountId:function:aidialer-api/invocations"
    
    # Add permission for API Gateway
    aws lambda add-permission --function-name aidialer-api --statement-id api-gateway-invoke --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:${accountId}:${apiId}/*/*"
    
    # Deploy API
    aws apigateway create-deployment --rest-api-id $apiId --stage-name prod
    
    Write-Host "✅ API Gateway deployed" -ForegroundColor Green
    
    # Output URLs
    Write-Host "`n🎉 Deployment Complete!" -ForegroundColor Green
    Write-Host "🌐 API URL: https://$apiId.execute-api.us-east-1.amazonaws.com/prod" -ForegroundColor Cyan
    Write-Host "📖 API Docs: https://$apiId.execute-api.us-east-1.amazonaws.com/prod/docs" -ForegroundColor Cyan
    Write-Host "❤️ Health Check: https://$apiId.execute-api.us-east-1.amazonaws.com/prod/health" -ForegroundColor Cyan
} else {
    Write-Host "❌ Failed to create API Gateway" -ForegroundColor Red
}

# Cleanup
Remove-Item "lambda-trust-policy.json" -ErrorAction SilentlyContinue
Remove-Item "lambda-deployment.zip" -ErrorAction SilentlyContinue
Remove-Item "lambda-package" -Recurse -ErrorAction SilentlyContinue

Write-Host "`nAI Dialer is now live on AWS Lambda!" -ForegroundColor Green 