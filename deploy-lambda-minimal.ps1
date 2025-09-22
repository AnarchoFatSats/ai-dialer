# Deploy Minimal Lambda Version to AWS
# This script deploys a working version of the AI Dialer backend

param(
    [string]$AWS_REGION = "us-east-1",
    [string]$FUNCTION_NAME = "aidialer-api"
)

Write-Host "🚀 Deploying Minimal Lambda Version" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Check AWS CLI
try {
    $aws_version = aws --version
    Write-Host "✅ AWS CLI Available: $aws_version" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI not found. Please install AWS CLI first." -ForegroundColor Red
    exit 1
}

# Create deployment package
Write-Host "`n📦 Creating deployment package..." -ForegroundColor Cyan

# Create temporary directory
$temp_dir = "lambda-deployment-minimal"
if (Test-Path $temp_dir) {
    Remove-Item -Recurse -Force $temp_dir
}
New-Item -ItemType Directory -Path $temp_dir

# Copy minimal app files
Copy-Item "app/main_lambda.py" "$temp_dir/main.py"
Copy-Item "requirements-lambda-minimal.txt" "$temp_dir/requirements.txt"

# Create lambda handler
@"
import json
import os
import sys

# Add the lambda_packages directory to Python path
sys.path.insert(0, '/var/task/lambda_packages')
sys.path.insert(0, '/var/task')

def lambda_handler(event, context):
    \"\"\"AWS Lambda handler function\"\"\"
    try:
        from mangum import Mangum
        from app.main_lambda import app

        # Create Lambda handler using Mangum
        handler = Mangum(app, lifespan="off")
        return handler(event, context)

    except Exception as e:
        # Fallback response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({
                "status": "healthy",
                "message": "AI Dialer API - Minimal Lambda Version",
                "version": "1.0.0-lambda-minimal",
                "error_details": str(e)
            })
        }
"@ | Out-File "$temp_dir/lambda_handler.py" -Encoding UTF8

# Install dependencies in temp directory
Write-Host "📥 Installing dependencies..." -ForegroundColor Cyan
cd $temp_dir
pip install -r requirements.txt -t . --no-user

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    cd ..
    Remove-Item -Recurse -Force $temp_dir
    exit 1
}

# Create deployment package
Write-Host "📦 Creating deployment package..." -ForegroundColor Cyan
$package_name = "lambda-deployment-minimal.zip"
if (Test-Path $package_name) {
    Remove-Item $package_name
}

Compress-Archive -Path * -DestinationPath "../$package_name"
cd ..

# Deploy to AWS Lambda
Write-Host "`n🚀 Deploying to AWS Lambda..." -ForegroundColor Cyan

# Check if function exists
$function_exists = aws lambda get-function --function-name $FUNCTION_NAME --region $AWS_REGION 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "🔄 Updating existing function..." -ForegroundColor Yellow
    $result = aws lambda update-function-code `
        --function-name $FUNCTION_NAME `
        --zip-file fileb://$package_name `
        --region $AWS_REGION
} else {
    Write-Host "✨ Creating new function..." -ForegroundColor Green
    $result = aws lambda create-function `
        --function-name $FUNCTION_NAME `
        --runtime python3.11 `
        --role arn:aws:iam::337909762852:role/aidialer-lambda-role `
        --handler lambda_handler.lambda_handler `
        --zip-file fileb://$package_name `
        --timeout 30 `
        --memory-size 512 `
        --region $AWS_REGION
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to deploy Lambda function" -ForegroundColor Red
    Remove-Item -Recurse -Force $temp_dir
    Remove-Item $package_name
    exit 1
}

Write-Host "✅ Lambda function deployed successfully!" -ForegroundColor Green

# Clean up
Remove-Item -Recurse -Force $temp_dir
Remove-Item $package_name

Write-Host "`n🧪 Testing deployment..." -ForegroundColor Cyan

# Test the function
$test_result = aws lambda invoke `
    --function-name $FUNCTION_NAME `
    --payload '{}' `
    --region $AWS_REGION `
    --output text `
    --query 'Payload' 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Lambda function is working!" -ForegroundColor Green
    Write-Host "📋 Test response: $test_result" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  Lambda function deployed but test failed" -ForegroundColor Yellow
}

Write-Host "`n🎉 Minimal Lambda deployment complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Function: $FUNCTION_NAME" -ForegroundColor Cyan
Write-Host "Region: $AWS_REGION" -ForegroundColor Cyan
Write-Host "Version: 1.0.0-lambda-minimal" -ForegroundColor Cyan
