import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_

from app.config import settings
from app.database import get_db
from app.models import Campaign, Lead, CallLog, DIDPool, CampaignAnalytics
from app.services.twilio_integration import twilio_service
from app.services.ai_conversation import ai_conversation_engine
from app.services.media_stream_handler import media_stream_handler
from app.services.did_management import did_management_service
from app.services.dnc_scrubbing import dnc_scrubbing_service
from app.services.cost_optimization import cost_optimization_service
from app.services.analytics_engine import analytics_engine

logger = logging.getLogger(__name__)

class CallStatus(Enum):
    QUEUED = "queued"
    DIALING = "dialing"
    RINGING = "ringing"
    ANSWERED = "answered"
    IN_PROGRESS = "in_progress"
    TRANSFERRING = "transferring"
    TRANSFERRED = "transferred"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    CANCELLED = "cancelled"

@dataclass
class CallRequest:
    campaign_id: int
    lead_id: int
    priority: int = 1
    scheduled_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3

class CallOrchestrationService:
    def __init__(self):
        self.call_queue: List[CallRequest] = []
        self.active_calls: Dict[int, Dict[str, Any]] = {}
        self.max_concurrent_calls = settings.MAX_CONCURRENT_CALLS
        self.is_running = False
        self.orchestration_task = None
        
    async def start_orchestration(self):
        """Start the call orchestration service"""
        if self.is_running:
            return
            
        self.is_running = True
        self.orchestration_task = asyncio.create_task(self._orchestration_loop())
        logger.info("Call orchestration service started")
        
    async def stop_orchestration(self):
        """Stop the call orchestration service"""
        self.is_running = False
        if self.orchestration_task:
            self.orchestration_task.cancel()
            try:
                await self.orchestration_task
            except asyncio.CancelledError:
                pass
        logger.info("Call orchestration service stopped")
        
    async def queue_call(self, campaign_id: int, lead_id: int, priority: int = 1, 
                        scheduled_time: Optional[datetime] = None) -> bool:
        """Queue a call for processing"""
        try:
            # Validate campaign and lead
            async with get_db() as db:
                campaign_query = select(Campaign).where(Campaign.id == campaign_id)
                campaign = await db.execute(campaign_query)
                campaign = campaign.scalar_one_or_none()
                
                if not campaign or campaign.status != 'active':
                    logger.warning(f"Campaign {campaign_id} not found or not active")
                    return False
                
                lead_query = select(Lead).where(Lead.id == lead_id)
                lead = await db.execute(lead_query)
                lead = lead.scalar_one_or_none()
                
                if not lead:
                    logger.warning(f"Lead {lead_id} not found")
                    return False
                
                # Check if lead is on DNC list
                if await dnc_scrubbing_service.is_dnc_number(lead.phone_number):
                    logger.info(f"Lead {lead_id} is on DNC list, skipping")
                    return False
                
                # Check calling hours
                if not self._is_calling_hours_valid(lead):
                    logger.info(f"Outside calling hours for lead {lead_id}")
                    return False
                
                # Check recent call history
                if await self._has_recent_call(lead_id):
                    logger.info(f"Lead {lead_id} has recent call, skipping")
                    return False
                
                # Create call request
                call_request = CallRequest(
                    campaign_id=campaign_id,
                    lead_id=lead_id,
                    priority=priority,
                    scheduled_time=scheduled_time
                )
                
                # Add to queue
                self.call_queue.append(call_request)
                
                # Sort queue by priority and scheduled time
                self.call_queue.sort(key=lambda x: (x.priority, x.scheduled_time or datetime.utcnow()))
                
                logger.info(f"Queued call for lead {lead_id} in campaign {campaign_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error queueing call: {e}")
            return False
    
    async def _orchestration_loop(self):
        """Main orchestration loop"""
        while self.is_running:
            try:
                # Process queue
                await self._process_call_queue()
                
                # Monitor active calls
                await self._monitor_active_calls()
                
                # Update metrics
                await self._update_system_metrics()
                
                # Check budget limits
                await self._check_budget_limits()
                
                # Wait before next iteration
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}")
                await asyncio.sleep(5)
    
    async def _process_call_queue(self):
        """Process queued calls"""
        try:
            current_calls = len(self.active_calls)
            
            # Process calls if under limit
            while (current_calls < self.max_concurrent_calls and 
                   self.call_queue and 
                   self.is_running):
                
                # Get next call from queue
                call_request = self.call_queue.pop(0)
                
                # Check if scheduled time has passed
                if (call_request.scheduled_time and 
                    call_request.scheduled_time > datetime.utcnow()):
                    # Put back in queue
                    self.call_queue.append(call_request)
                    break
                
                # Initiate call
                success = await self._initiate_call(call_request)
                
                if success:
                    current_calls += 1
                else:
                    # Handle retry logic
                    if call_request.retry_count < call_request.max_retries:
                        call_request.retry_count += 1
                        call_request.scheduled_time = datetime.utcnow() + timedelta(minutes=5)
                        self.call_queue.append(call_request)
                        logger.info(f"Retrying call for lead {call_request.lead_id} in 5 minutes")
                
        except Exception as e:
            logger.error(f"Error processing call queue: {e}")
    
    async def _initiate_call(self, call_request: CallRequest) -> bool:
        """Initiate a single call"""
        try:
            # Get available DID
            did = await did_management_service.get_available_did(call_request.campaign_id)
            if not did:
                logger.warning(f"No available DID for campaign {call_request.campaign_id}")
                return False
            
            # Pre-flight checks
            if not await self._pre_flight_checks(call_request):
                return False
            
            # Initiate call via Twilio
            call_result = await twilio_service.initiate_call(
                call_request.lead_id,
                call_request.campaign_id,
                did['id']
            )
            
            # Track active call
            self.active_calls[call_result['call_log_id']] = {
                'call_request': call_request,
                'call_result': call_result,
                'started': datetime.utcnow(),
                'status': CallStatus.DIALING
            }
            
            # Update DID usage
            await did_management_service.mark_did_in_use(did['id'])
            
            # Track cost
            await cost_optimization_service.track_call_cost(
                call_result['call_log_id'],
                'initiate'
            )
            
            logger.info(f"Initiated call {call_result['call_log_id']} for lead {call_request.lead_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error initiating call: {e}")
            return False
    
    async def _pre_flight_checks(self, call_request: CallRequest) -> bool:
        """Perform pre-flight checks before initiating call"""
        try:
            # Check budget
            if not await cost_optimization_service.check_budget_available(call_request.campaign_id):
                logger.warning(f"Budget exceeded for campaign {call_request.campaign_id}")
                return False
            
            # Check lead status
            async with get_db() as db:
                lead_query = select(Lead).where(Lead.id == call_request.lead_id)
                lead = await db.execute(lead_query)
                lead = lead.scalar_one_or_none()
                
                if not lead or lead.status != 'active':
                    logger.warning(f"Lead {call_request.lead_id} not active")
                    return False
            
            # Check campaign status
            async with get_db() as db:
                campaign_query = select(Campaign).where(Campaign.id == call_request.campaign_id)
                campaign = await db.execute(campaign_query)
                campaign = campaign.scalar_one_or_none()
                
                if not campaign or campaign.status != 'active':
                    logger.warning(f"Campaign {call_request.campaign_id} not active")
                    return False
            
            # Check calling hours
            if not self._is_calling_hours_valid(lead):
                logger.info(f"Outside calling hours for lead {call_request.lead_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in pre-flight checks: {e}")
            return False
    
    async def _monitor_active_calls(self):
        """Monitor and update active calls"""
        try:
            calls_to_remove = []
            
            for call_log_id, call_data in self.active_calls.items():
                try:
                    # Check call status
                    current_status = await self._get_call_status(call_log_id)
                    
                    if current_status != call_data['status']:
                        # Status changed
                        await self._handle_status_change(call_log_id, call_data, current_status)
                        call_data['status'] = current_status
                    
                    # Check for timeouts
                    call_duration = (datetime.utcnow() - call_data['started']).total_seconds()
                    
                    if call_duration > 300:  # 5 minute timeout
                        logger.warning(f"Call {call_log_id} timed out after {call_duration} seconds")
                        await self._handle_call_timeout(call_log_id, call_data)
                        calls_to_remove.append(call_log_id)
                    
                    # Check if call is completed
                    if current_status in [CallStatus.COMPLETED, CallStatus.FAILED, 
                                        CallStatus.BUSY, CallStatus.NO_ANSWER, 
                                        CallStatus.CANCELLED]:
                        await self._handle_call_completion(call_log_id, call_data)
                        calls_to_remove.append(call_log_id)
                
                except Exception as e:
                    logger.error(f"Error monitoring call {call_log_id}: {e}")
                    calls_to_remove.append(call_log_id)
            
            # Remove completed calls
            for call_log_id in calls_to_remove:
                if call_log_id in self.active_calls:
                    del self.active_calls[call_log_id]
                    
        except Exception as e:
            logger.error(f"Error monitoring active calls: {e}")
    
    async def _get_call_status(self, call_log_id: int) -> CallStatus:
        """Get current status of a call"""
        try:
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if not call_log:
                    return CallStatus.FAILED
                
                # Map Twilio status to our status
                status_map = {
                    'initiated': CallStatus.DIALING,
                    'ringing': CallStatus.RINGING,
                    'answered': CallStatus.ANSWERED,
                    'in-progress': CallStatus.IN_PROGRESS,
                    'completed': CallStatus.COMPLETED,
                    'failed': CallStatus.FAILED,
                    'busy': CallStatus.BUSY,
                    'no-answer': CallStatus.NO_ANSWER,
                    'canceled': CallStatus.CANCELLED
                }
                
                return status_map.get(call_log.call_status, CallStatus.FAILED)
                
        except Exception as e:
            logger.error(f"Error getting call status: {e}")
            return CallStatus.FAILED
    
    async def _handle_status_change(self, call_log_id: int, call_data: Dict[str, Any], 
                                  new_status: CallStatus):
        """Handle call status changes"""
        try:
            logger.info(f"Call {call_log_id} status changed to {new_status.value}")
            
            if new_status == CallStatus.ANSWERED:
                # Call was answered - start AI conversation
                await ai_conversation_engine.start_conversation(call_log_id)
                
            elif new_status == CallStatus.IN_PROGRESS:
                # Call is in progress - monitor for transfer signals
                pass
                
            elif new_status == CallStatus.TRANSFERRING:
                # Call is being transferred
                pass
                
            # Update analytics
            await analytics_engine.record_call_event(call_log_id, new_status.value)
            
        except Exception as e:
            logger.error(f"Error handling status change: {e}")
    
    async def _handle_call_timeout(self, call_log_id: int, call_data: Dict[str, Any]):
        """Handle call timeout"""
        try:
            logger.warning(f"Handling timeout for call {call_log_id}")
            
            # Hang up the call
            await twilio_service.hangup_call(call_log_id)
            
            # Close media stream
            await media_stream_handler.close_stream(call_log_id)
            
            # End AI conversation
            await ai_conversation_engine.end_conversation(call_log_id)
            
        except Exception as e:
            logger.error(f"Error handling call timeout: {e}")
    
    async def _handle_call_completion(self, call_log_id: int, call_data: Dict[str, Any]):
        """Handle call completion"""
        try:
            logger.info(f"Handling completion for call {call_log_id}")
            
            # End AI conversation
            await ai_conversation_engine.end_conversation(call_log_id)
            
            # Close media stream
            await media_stream_handler.close_stream(call_log_id)
            
            # Release DID
            call_request = call_data['call_request']
            await did_management_service.release_did(call_request.campaign_id)
            
            # Update analytics
            await analytics_engine.record_call_completion(call_log_id)
            
            # Track final cost
            await cost_optimization_service.track_call_cost(call_log_id, 'complete')
            
        except Exception as e:
            logger.error(f"Error handling call completion: {e}")
    
    async def _update_system_metrics(self):
        """Update system-wide metrics"""
        try:
            # Update call metrics
            total_active = len(self.active_calls)
            queue_size = len(self.call_queue)
            
            # Update analytics
            await analytics_engine.update_system_metrics({
                'active_calls': total_active,
                'queue_size': queue_size,
                'timestamp': datetime.utcnow()
            })
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    async def _check_budget_limits(self):
        """Check and enforce budget limits"""
        try:
            # Get all active campaigns
            async with get_db() as db:
                campaigns_query = select(Campaign).where(Campaign.status == 'active')
                campaigns = await db.execute(campaigns_query)
                campaigns = campaigns.scalars().all()
                
                for campaign in campaigns:
                    # Check if budget is exceeded
                    if not await cost_optimization_service.check_budget_available(campaign.id):
                        # Pause campaign
                        await self._pause_campaign(campaign.id)
                        
        except Exception as e:
            logger.error(f"Error checking budget limits: {e}")
    
    async def _pause_campaign(self, campaign_id: int):
        """Pause a campaign due to budget limits"""
        try:
            async with get_db() as db:
                # Update campaign status
                campaign_update = update(Campaign).where(Campaign.id == campaign_id).values(
                    status='paused',
                    paused_reason='budget_exceeded',
                    updated_at=datetime.utcnow()
                )
                await db.execute(campaign_update)
                await db.commit()
                
                # Remove campaign calls from queue
                self.call_queue = [
                    call for call in self.call_queue 
                    if call.campaign_id != campaign_id
                ]
                
                logger.warning(f"Paused campaign {campaign_id} due to budget limits")
                
        except Exception as e:
            logger.error(f"Error pausing campaign: {e}")
    
    def _is_calling_hours_valid(self, lead: Any) -> bool:
        """Check if current time is within valid calling hours"""
        try:
            # Get current time in lead's timezone
            # This is a simplified check - in production, implement proper timezone handling
            current_hour = datetime.utcnow().hour
            
            # Standard calling hours: 9 AM to 8 PM
            return 9 <= current_hour <= 20
            
        except Exception as e:
            logger.error(f"Error checking calling hours: {e}")
            return False
    
    async def _has_recent_call(self, lead_id: int) -> bool:
        """Check if lead has been called recently"""
        try:
            async with get_db() as db:
                # Check for calls in last 24 hours
                recent_time = datetime.utcnow() - timedelta(hours=24)
                
                recent_call_query = select(CallLog).where(
                    and_(
                        CallLog.lead_id == lead_id,
                        CallLog.call_start >= recent_time
                    )
                )
                
                recent_call = await db.execute(recent_call_query)
                recent_call = recent_call.scalar_one_or_none()
                
                return recent_call is not None
                
        except Exception as e:
            logger.error(f"Error checking recent calls: {e}")
            return False
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            'queue_size': len(self.call_queue),
            'active_calls': len(self.active_calls),
            'max_concurrent_calls': self.max_concurrent_calls,
            'is_running': self.is_running
        }
    
    async def get_active_calls_info(self) -> List[Dict[str, Any]]:
        """Get information about active calls"""
        return [
            {
                'call_log_id': call_log_id,
                'campaign_id': call_data['call_request'].campaign_id,
                'lead_id': call_data['call_request'].lead_id,
                'status': call_data['status'].value,
                'duration': (datetime.utcnow() - call_data['started']).total_seconds()
            }
            for call_log_id, call_data in self.active_calls.items()
        ]
    
    async def cancel_call(self, call_log_id: int) -> bool:
        """Cancel an active call"""
        try:
            if call_log_id in self.active_calls:
                # Hang up the call
                await twilio_service.hangup_call(call_log_id)
                
                # Handle completion
                await self._handle_call_completion(call_log_id, self.active_calls[call_log_id])
                
                # Remove from active calls
                del self.active_calls[call_log_id]
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling call: {e}")
            return False

# Global instance
call_orchestration_service = CallOrchestrationService() 