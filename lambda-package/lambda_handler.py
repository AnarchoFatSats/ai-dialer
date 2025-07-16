"""
Enhanced AWS Lambda handler with conversational training support
"""

import json
import os
import uuid
from datetime import datetime
from urllib.parse import unquote

def lambda_handler(event, context):
    """
    Enhanced Lambda handler with conversational training support
    """
    try:
        # Get request details
        path = event.get('path', event.get('rawPath', ''))
        method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', 'GET'))
        
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        
        # Parse body for POST requests
        body = {}
        if method == 'POST' and event.get('body'):
            try:
                body = json.loads(event.get('body', '{}'))
            except json.JSONDecodeError:
                body = {}
        
        # CORS headers
        cors_headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
        
        # Handle OPTIONS preflight requests
        if method == 'OPTIONS':
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({"message": "OK"})
            }
        
        # Health check endpoint
        if path == '/health':
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "1.0.0-production",
                    "environment": os.environ.get("ENVIRONMENT", "production"),
                    "lambda_context": {
                        "function_name": context.function_name,
                        "function_version": context.function_version,
                        "memory_limit": context.memory_limit_in_mb,
                        "request_id": context.aws_request_id
                    }
                })
            }
        
        # Conversational training start endpoint
        if path == '/conversational-training/start' and method == 'POST':
            session_id = str(uuid.uuid4())
            
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({
                    "session_id": session_id,
                    "message": "Hi! My name is Reach. I'm here to walk you through building the perfect campaign so the AI can create amazing prompts for a great agent ready to go. Let's start by understanding what you want to achieve with your calling campaign. What type of business are you calling for?",
                    "state": "initial",
                    "suggested_responses": [
                        "Lead Generation",
                        "Sales Outreach",
                        "Customer Support",
                        "Market Research", 
                        "Appointment Setting",
                        "Follow-up Calls"
                    ]
                })
            }
        
        # Conversational training continue endpoint
        if path == '/conversational-training/continue' and method == 'POST':
            session_id = body.get('session_id')
            message = body.get('message', '')
            
            # Simple conversation flow logic
            response_message = ""
            suggested_responses = []
            
            if "lead generation" in message.lower():
                response_message = "Excellent! Lead generation is a powerful strategy. Now, let me understand your target audience better. Who are you trying to reach? For example, are you targeting homeowners, business owners, or a specific demographic?"
                suggested_responses = ["Homeowners", "Business owners", "Healthcare professionals", "Small business owners"]
            elif "sales outreach" in message.lower():
                response_message = "Great choice! Sales outreach can be highly effective. What product or service are you selling? This will help me tailor the perfect conversation flow for your prospects."
                suggested_responses = ["Software/SaaS", "Insurance", "Solar panels", "Financial services"]
            elif "homeowners" in message.lower():
                response_message = "Perfect! Homeowners are an excellent target. What's the main problem or need you're solving for them? This will help me create compelling conversation starters."
                suggested_responses = ["Energy savings", "Home security", "Home improvement", "Property value"]
            elif "business owners" in message.lower():
                response_message = "Excellent! Business owners are decision-makers. What's your value proposition? What specific business challenge are you helping them solve?"
                suggested_responses = ["Cost reduction", "Revenue growth", "Operational efficiency", "Compliance"]
            else:
                response_message = "That's great information! Let me help you develop this further. What's the main benefit or outcome you want prospects to achieve? This will help me create the perfect conversation flow."
                suggested_responses = ["Schedule a consultation", "Get a free quote", "Learn more about benefits", "Start a free trial"]
            
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({
                    "session_id": session_id,
                    "message": response_message,
                    "state": "understanding_goal",
                    "suggested_responses": suggested_responses
                })
            }
        
        # Analytics dashboard endpoint
        if path == '/analytics/dashboard' and method == 'GET':
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({
                    "active_calls": 12,
                    "today_transfers": 45,
                    "today_revenue": 8750,
                    "cost_per_transfer": 0.125,
                    "transfer_rate": 18.5,
                    "ai_efficiency": 94.2,
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
        
        # Analytics learning stats endpoint
        if path == '/analytics/learning-stats' and method == 'GET':
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({
                    "progress": 78,
                    "successRate": 22.5,
                    "totalCalls": 1247,
                    "conversions": 281,
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
        
        # Default response for unknown paths
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({
                "message": "AI Dialer API - Production Ready",
                "status": "healthy",
                "environment": "production",
                "path": path,
                "method": method,
                "timestamp": datetime.utcnow().isoformat(),
                "available_endpoints": [
                    "/health",
                    "/conversational-training/start",
                    "/conversational-training/continue", 
                    "/analytics/dashboard",
                    "/analytics/learning-stats"
                ]
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