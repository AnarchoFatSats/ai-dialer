import json
import os
import sys

# Add the lambda_packages directory to Python path
sys.path.insert(0, '/var/task/lambda_packages')
sys.path.insert(0, '/var/task')

# Set environment for Lambda
os.environ["AWS_LAMBDA_FUNCTION_NAME"] = "aidialer-api"
os.environ["DATABASE_URL"] = ""
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
        # Fallback if enhanced version fails
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "degraded",
                "message": f"Enhanced features unavailable: {str(e)}",
                "version": "1.0.0-fallback"
            })
        }
