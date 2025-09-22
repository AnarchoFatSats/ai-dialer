"""
Minimal FastAPI application for Lambda deployment
Simplified version with core functionality only
"""

import logging
import asyncio
import json
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Dialer - Minimal Lambda Version",
    description="Minimal AI Dialer API for Lambda deployment",
    version="1.0.0-lambda"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0-lambda",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "AI Dialer API - Minimal Lambda Version",
        "endpoints": [
            "/health",
            "/campaigns",
            "/analytics/dashboard"
        ]
    }

@app.get("/campaigns")
async def get_campaigns():
    """Get campaigns endpoint"""
    return {
        "campaigns": [],
        "message": "Campaigns endpoint - ready for enhancement"
    }

@app.post("/campaigns")
async def create_campaign(campaign_data: dict):
    """Create campaign endpoint"""
    return {
        "message": "Campaign creation endpoint - ready for enhancement",
        "received": campaign_data
    }

@app.get("/analytics/dashboard")
async def get_analytics():
    """Analytics dashboard endpoint"""
    return {
        "active_calls": 0,
        "today_transfers": 0,
        "today_revenue": 0.0,
        "message": "Analytics dashboard - ready for enhancement"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Dialer API - Minimal Lambda Version",
        "status": "operational",
        "version": "1.0.0-lambda"
    }

# Create Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler function"""
    try:
        from mangum import Mangum
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
                "message": "AI Dialer API - Fallback Mode",
                "version": "1.0.0-lambda-fallback",
                "error": str(e)
            })
        }
