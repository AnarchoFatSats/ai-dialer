"""
Minimal AWS Lambda handler for testing
"""

import json
import os
from datetime import datetime

def lambda_handler(event, context):
    """
    Minimal Lambda handler for testing
    """
    try:
        # Basic health check response
        if event.get('path') == '/health' or event.get('rawPath') == '/health':
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "1.0.0-minimal",
                    "environment": os.environ.get("ENVIRONMENT", "unknown"),
                    "lambda_context": {
                        "function_name": context.function_name,
                        "function_version": context.function_version,
                        "memory_limit": context.memory_limit_in_mb,
                        "request_id": context.aws_request_id
                    }
                })
            }
        
        # Default response for other paths
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "message": "AI Dialer API - Minimal Version",
                "path": event.get('path', event.get('rawPath', 'unknown')),
                "method": event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', 'unknown')),
                "timestamp": datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        } 