"""
AI Dialer Main Application
FastAPI application with Phase 3 optimization features.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from app.config import settings
from app.database import get_db, AsyncSessionLocal
from app.models import *
from sqlalchemy import select
from app.services.campaign_management import get_campaign_management_service
from app.services.dnc_scrubbing import get_dnc_scrubbing_service
from app.services.analytics_engine import get_analytics_engine
from app.services.quality_scoring import get_quality_scoring_service
from app.services.cost_optimization import get_cost_optimization_engine
from app.services.twilio_integration import twilio_service
from app.services.ai_conversation import ai_conversation_engine
from app.services.media_stream_handler import media_stream_handler
from app.services.call_orchestration import call_orchestration_service
from app.services.did_management import did_management_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    script_template: str
    max_concurrent_calls: Optional[int] = 100
    max_daily_budget: Optional[float] = 1000.0
    cost_per_minute_limit: Optional[float] = 0.025
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    daily_start_hour: Optional[int] = 8
    daily_end_hour: Optional[int] = 21
    timezone: Optional[str] = "America/New_York"
    ab_test_enabled: Optional[bool] = False
    ab_test_variants: Optional[Dict[str, Any]] = {}

class LeadUpload(BaseModel):
    campaign_id: str
    leads: List[Dict[str, Any]]

class DNCRequest(BaseModel):
    phone_numbers: Optional[List[str]] = None
    full_scrub: Optional[bool] = False

class QualityEvaluationRequest(BaseModel):
    call_log_ids: List[str]

class CostTrackingRequest(BaseModel):
    campaign_id: str

class CallInitiateRequest(BaseModel):
    campaign_id: str
    lead_id: str
    priority: int = 1
    scheduled_time: Optional[datetime] = None

class CallTransferRequest(BaseModel):
    call_log_id: str
    transfer_number: str

class DIDInitializeRequest(BaseModel):
    campaign_id: str
    area_codes: List[str]
    count_per_area: int = 5

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Dialer application")
    
    # Initialize services with graceful error handling
    startup_errors = []
    
    # Test database connection
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(select(1))
        logger.info("Database connection established")
    except Exception as e:
        error_msg = f"Database connection failed: {e}"
        logger.error(error_msg)
        startup_errors.append(error_msg)
        
        # For AWS deployment, database connection is critical
        if not settings.debug:
            raise
    
    # Test Redis connection (optional in development)
    try:
        # Add Redis connection test here if needed
        logger.info("Redis connection check skipped (not implemented)")
    except Exception as e:
        error_msg = f"Redis connection failed: {e}"
        logger.warning(error_msg)
        startup_errors.append(error_msg)
    
    # Start call orchestration service
    try:
        await call_orchestration_service.start_orchestration()
        logger.info("Call orchestration service started")
    except Exception as e:
        error_msg = f"Call orchestration service failed to start: {e}"
        logger.error(error_msg)
        startup_errors.append(error_msg)
        
        # Don't fail startup for orchestration service in development
        if not settings.debug:
            raise
    
    # Log startup summary
    if startup_errors:
        logger.warning(f"Application started with {len(startup_errors)} warnings:")
        for error in startup_errors:
            logger.warning(f"  - {error}")
        if settings.debug:
            logger.info("Running in development mode - some service failures are acceptable")
    else:
        logger.info("All services started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Dialer application")
    
    # Stop call orchestration service
    try:
        await call_orchestration_service.stop_orchestration()
        logger.info("Call orchestration service stopped")
    except Exception as e:
        logger.error(f"Error stopping call orchestration service: {e}")
        # Don't fail shutdown for orchestration service

# Create FastAPI app
app = FastAPI(
    title="AI Dialer API",
    description="AI-powered outbound voice dialer with advanced optimization",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint with AWS service status."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {}
    }
    
    # Check database connection
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(select(1))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis connection (if configured)
    try:
        # Add Redis health check here if needed
        health_status["services"]["redis"] = "not_implemented"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
    
    # Check external services
    health_status["services"]["twilio"] = "configured" if settings.twilio_account_sid != "your_account_sid" else "not_configured"
    health_status["services"]["anthropic"] = "configured" if settings.anthropic_api_key != "your_anthropic_key" else "not_configured"
    health_status["services"]["deepgram"] = "configured" if settings.deepgram_api_key != "your_deepgram_key" else "not_configured"
    health_status["services"]["elevenlabs"] = "configured" if settings.elevenlabs_api_key != "your_elevenlabs_key" else "not_configured"
    
    return health_status

# Campaign Management Endpoints
@app.post("/campaigns", tags=["Campaign Management"], response_model=Dict[str, Any])
async def create_campaign(
    campaign_data: CampaignCreate,
    campaign_service = Depends(get_campaign_management_service)
):
    """Create a new campaign with optimization features."""
    try:
        campaign = await campaign_service.create_campaign(campaign_data.dict())
        return {
            "success": True,
            "campaign_id": str(campaign.id),
            "name": campaign.name,
            "status": campaign.status.value,
            "created_at": campaign.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/campaigns/{campaign_id}/leads", tags=["Campaign Management"])
async def upload_leads(
    campaign_id: str,
    leads_data: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    campaign_service = Depends(get_campaign_management_service),
    dnc_service = Depends(get_dnc_scrubbing_service)
):
    """Upload leads to a campaign with DNC scrubbing."""
    try:
        # Upload leads
        results = await campaign_service.upload_leads(uuid.UUID(campaign_id), leads_data)
        
        # Schedule DNC scrubbing in background
        lead_phones = [lead.get('phone') for lead in leads_data if lead.get('phone')]
        if lead_phones:
            background_tasks.add_task(dnc_service.scrub_lead_list, lead_phones)
        
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        logger.error(f"Error uploading leads: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/campaigns/{campaign_id}/start", tags=["Campaign Management"])
async def start_campaign(
    campaign_id: str,
    campaign_service = Depends(get_campaign_management_service)
):
    """Start a campaign after pre-flight checks."""
    try:
        success = await campaign_service.start_campaign(uuid.UUID(campaign_id))
        if success:
            return {"success": True, "message": "Campaign started successfully"}
        else:
            raise HTTPException(status_code=400, detail="Campaign failed pre-flight checks")
    except Exception as e:
        logger.error(f"Error starting campaign: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/campaigns/{campaign_id}/pause", tags=["Campaign Management"])
async def pause_campaign(
    campaign_id: str,
    reason: Optional[str] = None,
    campaign_service = Depends(get_campaign_management_service)
):
    """Pause a campaign."""
    try:
        success = await campaign_service.pause_campaign(uuid.UUID(campaign_id), reason)
        if success:
            return {"success": True, "message": "Campaign paused successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to pause campaign")
    except Exception as e:
        logger.error(f"Error pausing campaign: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/campaigns/{campaign_id}/performance", tags=["Campaign Management"])
async def get_campaign_performance(
    campaign_id: str,
    campaign_service = Depends(get_campaign_management_service)
):
    """Get comprehensive campaign performance metrics."""
    try:
        performance = await campaign_service.get_campaign_performance(uuid.UUID(campaign_id))
        return performance
    except Exception as e:
        logger.error(f"Error getting campaign performance: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/campaigns", tags=["Campaign Management"])
async def list_campaigns(
    status: Optional[str] = None,
    campaign_service = Depends(get_campaign_management_service)
):
    """List campaigns with optional status filter."""
    try:
        status_filter = CampaignStatus(status) if status else None
        campaigns = await campaign_service.list_campaigns(status_filter)
        
        return {
            "campaigns": [
                {
                    "id": str(campaign.id),
                    "name": campaign.name,
                    "status": campaign.status.value,
                    "total_leads": campaign.total_leads,
                    "total_cost": campaign.total_cost,
                    "created_at": campaign.created_at.isoformat()
                }
                for campaign in campaigns
            ]
        }
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# DNC Scrubbing Endpoints
@app.post("/dnc/scrub", tags=["DNC Compliance"])
async def dnc_scrub(
    request: DNCRequest,
    background_tasks: BackgroundTasks,
    dnc_service = Depends(get_dnc_scrubbing_service)
):
    """Perform DNC scrubbing on phone numbers or full registry update."""
    try:
        if request.full_scrub:
            # Schedule full DNC scrub in background
            background_tasks.add_task(dnc_service.full_dnc_scrub)
            return {
                "success": True,
                "message": "Full DNC scrub scheduled",
                "estimated_completion": "5-10 minutes"
            }
        elif request.phone_numbers:
            # Scrub specific phone numbers
            results = {}
            for phone in request.phone_numbers:
                is_dnc, source = await dnc_service.check_phone_dnc_status(phone)
                results[phone] = {"is_dnc": is_dnc, "source": source}
            
            return {
                "success": True,
                "results": results
            }
        else:
            raise HTTPException(status_code=400, detail="Must specify phone_numbers or full_scrub")
            
    except Exception as e:
        logger.error(f"Error in DNC scrub: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/dnc/suppress", tags=["DNC Compliance"])
async def add_suppression_numbers(
    phone_numbers: List[str],
    dnc_service = Depends(get_dnc_scrubbing_service)
):
    """Add phone numbers to company suppression list."""
    try:
        added_count = await dnc_service.add_company_suppression_numbers(phone_numbers)
        return {
            "success": True,
            "added_count": added_count,
            "message": f"Added {added_count} numbers to suppression list"
        }
    except Exception as e:
        logger.error(f"Error adding suppression numbers: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Analytics Endpoints
@app.get("/analytics/dashboard", tags=["Analytics"])
async def get_realtime_dashboard(
    analytics_engine = Depends(get_analytics_engine)
):
    """Get real-time dashboard metrics."""
    try:
        dashboard = await analytics_engine.get_realtime_dashboard()
        return dashboard
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/campaigns/{campaign_id}", tags=["Analytics"])
async def get_campaign_analytics(
    campaign_id: str,
    days: int = 7,
    analytics_engine = Depends(get_analytics_engine)
):
    """Get comprehensive analytics for a specific campaign."""
    try:
        analytics = await analytics_engine.get_campaign_analytics(uuid.UUID(campaign_id), days)
        return analytics
    except Exception as e:
        logger.error(f"Error getting campaign analytics: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/analytics/predictions/{campaign_id}", tags=["Analytics"])
async def get_predictive_insights(
    campaign_id: str,
    analytics_engine = Depends(get_analytics_engine)
):
    """Get predictive insights for campaign optimization."""
    try:
        insights = await analytics_engine.get_predictive_insights(uuid.UUID(campaign_id))
        return insights
    except Exception as e:
        logger.error(f"Error getting predictive insights: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Quality Scoring Endpoints
@app.post("/quality/evaluate", tags=["Quality Scoring"])
async def evaluate_call_quality(
    request: QualityEvaluationRequest,
    background_tasks: BackgroundTasks,
    quality_service = Depends(get_quality_scoring_service)
):
    """Evaluate call quality for specified call logs."""
    try:
        call_log_ids = [uuid.UUID(id_str) for id_str in request.call_log_ids]
        
        # Schedule batch evaluation in background
        background_tasks.add_task(quality_service.batch_evaluate_quality, call_log_ids)
        
        return {
            "success": True,
            "message": f"Quality evaluation scheduled for {len(call_log_ids)} calls",
            "estimated_completion": "2-5 minutes"
        }
    except Exception as e:
        logger.error(f"Error scheduling quality evaluation: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/quality/trends", tags=["Quality Scoring"])
async def get_quality_trends(
    campaign_id: Optional[str] = None,
    days: int = 7,
    quality_service = Depends(get_quality_scoring_service)
):
    """Get quality trends and analytics."""
    try:
        campaign_uuid = uuid.UUID(campaign_id) if campaign_id else None
        trends = await quality_service.get_quality_trends(campaign_uuid, days)
        return trends
    except Exception as e:
        logger.error(f"Error getting quality trends: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Cost Optimization Endpoints
@app.post("/cost/track/{campaign_id}", tags=["Cost Optimization"])
async def track_campaign_costs(
    campaign_id: str,
    cost_engine = Depends(get_cost_optimization_engine)
):
    """Track real-time costs for a campaign."""
    try:
        cost_metrics = await cost_engine.track_realtime_costs(uuid.UUID(campaign_id))
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "cost_metrics": {
                "total_cost": cost_metrics.total_cost,
                "cost_per_call": cost_metrics.cost_per_call,
                "cost_per_transfer": cost_metrics.cost_per_transfer,
                "cost_per_minute": cost_metrics.cost_per_minute,
                "budget_utilization": cost_metrics.budget_utilization,
                "projected_daily_cost": cost_metrics.projected_daily_cost,
                "efficiency_score": cost_metrics.efficiency_score
            },
            "alerts": cost_metrics.alerts
        }
    except Exception as e:
        logger.error(f"Error tracking costs: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/cost/optimization/{campaign_id}", tags=["Cost Optimization"])
async def get_cost_optimization_report(
    campaign_id: str,
    days: int = 7,
    cost_engine = Depends(get_cost_optimization_engine)
):
    """Get comprehensive cost optimization report."""
    try:
        report = await cost_engine.get_cost_optimization_report(uuid.UUID(campaign_id), days)
        return report
    except Exception as e:
        logger.error(f"Error getting cost optimization report: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# AI Voice Calling Endpoints
@app.post("/calls/initiate", tags=["AI Voice Calling"])
async def initiate_call(
    request: CallInitiateRequest
):
    """Initiate an AI voice call."""
    try:
        # Queue the call for processing
        success = await call_orchestration_service.queue_call(
            int(request.campaign_id),
            int(request.lead_id),
            request.priority,
            request.scheduled_time
        )
        
        if success:
            return {"success": True, "message": "Call queued successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to queue call")
    except Exception as e:
        logger.error(f"Error initiating call: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calls/transfer", tags=["AI Voice Calling"])
async def transfer_call(
    request: CallTransferRequest
):
    """Transfer an active call to human agent."""
    try:
        result = await twilio_service.transfer_call(
            int(request.call_log_id),
            request.transfer_number
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error transferring call: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/calls/active", tags=["AI Voice Calling"])
async def get_active_calls():
    """Get list of active calls."""
    try:
        active_calls = await call_orchestration_service.get_active_calls_info()
        return {"active_calls": active_calls}
    except Exception as e:
        logger.error(f"Error getting active calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calls/queue-status", tags=["AI Voice Calling"])
async def get_queue_status():
    """Get current call queue status."""
    try:
        status = await call_orchestration_service.get_queue_status()
        return status
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calls/{call_log_id}/cancel", tags=["AI Voice Calling"])
async def cancel_call(call_log_id: str):
    """Cancel an active call."""
    try:
        success = await call_orchestration_service.cancel_call(int(call_log_id))
        if success:
            return {"success": True, "message": "Call cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel call")
    except Exception as e:
        logger.error(f"Error cancelling call: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# DID Management Endpoints
@app.post("/did/initialize", tags=["DID Management"])
async def initialize_did_pool(
    request: DIDInitializeRequest
):
    """Initialize DID pool for a campaign."""
    try:
        result = await did_management_service.initialize_did_pool(
            int(request.campaign_id),
            request.area_codes,
            request.count_per_area
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error initializing DID pool: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/did/rotate/{campaign_id}", tags=["DID Management"])
async def rotate_dids(campaign_id: str):
    """Rotate DIDs for a campaign."""
    try:
        result = await did_management_service.rotate_dids(int(campaign_id))
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error rotating DIDs: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/did/status/{campaign_id}", tags=["DID Management"])
async def get_did_pool_status(campaign_id: str):
    """Get DID pool status for a campaign."""
    try:
        status = await did_management_service.get_did_pool_status(int(campaign_id))
        return status
    except Exception as e:
        logger.error(f"Error getting DID pool status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/did/health/{did_id}", tags=["DID Management"])
async def analyze_did_health(did_id: str):
    """Analyze health of a specific DID."""
    try:
        health_score = await did_management_service.analyze_did_health(int(did_id))
        return {
            "did_id": health_score.did_id,
            "phone_number": health_score.phone_number,
            "health_score": health_score.health_score,
            "answer_rate": health_score.answer_rate,
            "spam_complaints": health_score.spam_complaints,
            "carrier_filtering": health_score.carrier_filtering,
            "reputation_score": health_score.reputation_score,
            "recommendation": health_score.recommendation
        }
    except Exception as e:
        logger.error(f"Error analyzing DID health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time media streaming
@app.websocket("/ws/media-stream/{call_log_id}")
async def websocket_media_stream(websocket, call_log_id: str):
    """WebSocket endpoint for Twilio Media Streams."""
    await media_stream_handler.handle_media_stream(websocket, f"/ws/media-stream/{call_log_id}")

# Twilio Webhook Endpoints
@app.post("/webhooks/twilio/call-answer/{call_log_id}", tags=["Webhooks"])
async def handle_call_answer_webhook(call_log_id: str):
    """Handle Twilio call answer webhook."""
    try:
        twiml = await twilio_service.generate_call_answer_twiml(int(call_log_id))
        from fastapi.responses import Response
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        logger.error(f"Error handling call answer webhook: {e}")
        # Return fallback TwiML
        return Response(content="<Response><Say>Thank you for your time. Goodbye.</Say><Hangup/></Response>", media_type="application/xml")

@app.post("/webhooks/twilio/call-status/{call_log_id}", tags=["Webhooks"])
async def handle_call_status_webhook(
    call_log_id: str,
    background_tasks: BackgroundTasks,
    request: Dict[str, Any]
):
    """Handle Twilio call status webhook."""
    try:
        background_tasks.add_task(
            twilio_service.handle_call_status_webhook,
            int(call_log_id),
            request
        )
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error handling call status webhook: {e}")
        return {"status": "error", "message": str(e)}

# Webhook Endpoints (for Twilio integration - legacy)
@app.post("/webhooks/call-status", tags=["Webhooks"])
async def handle_call_status_webhook_legacy(
    # Twilio webhook parameters would be parsed here
    background_tasks: BackgroundTasks
):
    """Handle Twilio call status webhooks (legacy)."""
    try:
        # TODO: Parse Twilio webhook data
        # TODO: Update call log in database
        # TODO: Trigger quality scoring if call completed
        # TODO: Update cost tracking
        
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error handling call status webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/voice-insights", tags=["Webhooks"])
async def handle_voice_insights_webhook(
    background_tasks: BackgroundTasks
):
    """Handle Twilio Voice Insights webhooks."""
    try:
        # TODO: Parse Voice Insights data (607/608 blocks)
        # TODO: Update DID reputation scores
        # TODO: Trigger DID rotation if needed
        
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error handling voice insights webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await websocket.accept()
    
    try:
        while True:
            # TODO: Send real-time dashboard updates
            # TODO: Send cost alerts
            # TODO: Send quality alerts
            # TODO: Send DID health updates
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 