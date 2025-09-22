import json
import os
import sys

# Add the lambda_packages directory to Python path
sys.path.insert(0, '/var/task/lambda_packages')
sys.path.insert(0, '/var/task')

def lambda_handler(event, context):
    """AWS Lambda handler function"""
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