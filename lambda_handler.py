"""
AWS Lambda handler for FastAPI application
Runs the AI Dialer FastAPI app in AWS Lambda with API Gateway
"""

import json
import os
from mangum import Mangum
from app.main import app

# Set environment for Lambda
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("DEBUG", "false")

# Create Lambda handler using Mangum
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """
    AWS Lambda handler function
    """
    try:
        return handler(event, context)
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e)
            })
        } 