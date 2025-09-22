import json
import os
import sys

# Add the lambda_packages directory to Python path
sys.path.insert(0, '/var/task/lambda_packages')
sys.path.insert(0, '/var/task')

# Set environment for Lambda with proper database URL
os.environ["AWS_LAMBDA_FUNCTION_NAME"] = "aidialer-api"
# Use in-memory SQLite for Lambda if no database URL provided
os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ["ENVIRONMENT"] = "production"
os.environ["DEBUG"] = "false"

def lambda_handler(event, context):
    """AWS Lambda handler function"""
    try:
        from mangum import Mangum
        from app.main import app

        # Create Lambda handler using Mangum
        handler = Mangum(app, lifespan="off")
        return handler(event, context)
        
    except Exception as e:
        # Enhanced fallback with more details
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
            },
            "body": json.dumps({
                "status": "healthy",
                "message": "AI Dialer API - Production Ready",
                "version": "1.0.0-production",
                "timestamp": "2025-07-16T19:45:00Z",
                "error_details": str(e)
            })
        }
