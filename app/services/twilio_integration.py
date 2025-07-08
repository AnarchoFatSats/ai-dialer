import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import asyncio
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from twilio.base.exceptions import TwilioRestException

from app.config import settings
from app.database import get_db
from app.models import Campaign, Lead, CallLog, DIDPool

logger = logging.getLogger(__name__)

class TwilioIntegrationService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.base_url = settings.BASE_URL
        
    async def initiate_call(self, lead_id: int, campaign_id: int, did_id: int) -> Dict[str, Any]:
        """Initiate an outbound call with AI conversation flow"""
        try:
            async with get_db() as db:
                # Get lead and campaign info
                lead_query = select(Lead).where(Lead.id == lead_id)
                lead = await db.execute(lead_query)
                lead = lead.scalar_one_or_none()
                
                if not lead:
                    raise ValueError(f"Lead {lead_id} not found")
                
                campaign_query = select(Campaign).where(Campaign.id == campaign_id)
                campaign = await db.execute(campaign_query)
                campaign = campaign.scalar_one_or_none()
                
                if not campaign:
                    raise ValueError(f"Campaign {campaign_id} not found")
                
                # Get DID info
                did_query = select(DIDPool).where(DIDPool.id == did_id)
                did = await db.execute(did_query)
                did = did.scalar_one_or_none()
                
                if not did:
                    raise ValueError(f"DID {did_id} not found")
                
                # Create call log entry
                call_log = CallLog(
                    campaign_id=campaign_id,
                    lead_id=lead_id,
                    did_id=did_id,
                    phone_number=lead.phone_number,
                    call_start=datetime.utcnow(),
                    call_status='initiated'
                )
                db.add(call_log)
                await db.commit()
                await db.refresh(call_log)
                
                # Create TwiML for AI conversation
                twiml = VoiceResponse()
                
                # Set up Media Stream for real-time audio
                twiml.start().stream(
                    url=f"wss://{settings.DOMAIN}/ws/media-stream/{call_log.id}",
                    track="both_tracks"
                )
                
                # Initial greeting pause to let stream establish
                twiml.pause(length=1)
                
                # Set status callback URL
                status_callback = f"{self.base_url}/webhooks/twilio/call-status/{call_log.id}"
                
                # Make the call
                call = self.client.calls.create(
                    to=lead.phone_number,
                    from_=did.phone_number,
                    url=f"{self.base_url}/webhooks/twilio/call-answer/{call_log.id}",
                    status_callback=status_callback,
                    status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                    status_callback_method='POST',
                    timeout=30,
                    record=True if campaign.call_recording_enabled else False
                )
                
                # Update call log with Twilio SID
                call_log.twilio_call_sid = call.sid
                await db.commit()
                
                logger.info(f"Call initiated: {call.sid} to {lead.phone_number}")
                
                return {
                    'call_sid': call.sid,
                    'call_log_id': call_log.id,
                    'status': 'initiated',
                    'to_number': lead.phone_number,
                    'from_number': did.phone_number
                }
                
        except TwilioRestException as e:
            logger.error(f"Twilio error initiating call: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initiating call: {e}")
            raise
    
    async def generate_call_answer_twiml(self, call_log_id: int) -> str:
        """Generate TwiML for when call is answered"""
        try:
            async with get_db() as db:
                # Get call log and campaign info
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if not call_log:
                    raise ValueError(f"Call log {call_log_id} not found")
                
                campaign_query = select(Campaign).where(Campaign.id == call_log.campaign_id)
                campaign = await db.execute(campaign_query)
                campaign = campaign.scalar_one_or_none()
                
                response = VoiceResponse()
                
                # Start media stream for real-time AI conversation
                response.start().stream(
                    url=f"wss://{settings.DOMAIN}/ws/media-stream/{call_log_id}",
                    track="both_tracks"
                )
                
                # Brief pause to establish connection
                response.pause(length=1)
                
                # Initial AI greeting will be handled by the media stream
                # Keep the call alive with a long pause
                response.pause(length=300)  # 5 minutes max call duration
                
                # Update call status
                call_log.call_status = 'answered'
                call_log.call_answered = datetime.utcnow()
                await db.commit()
                
                return str(response)
                
        except Exception as e:
            logger.error(f"Error generating call answer TwiML: {e}")
            # Fallback TwiML
            response = VoiceResponse()
            response.say("Thank you for your time. Goodbye.")
            response.hangup()
            return str(response)
    
    async def handle_call_status_webhook(self, call_log_id: int, webhook_data: Dict[str, Any]) -> None:
        """Handle Twilio call status webhooks"""
        try:
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if not call_log:
                    logger.warning(f"Call log {call_log_id} not found for status webhook")
                    return
                
                status = webhook_data.get('CallStatus')
                duration = webhook_data.get('CallDuration')
                
                # Update call log based on status
                if status == 'ringing':
                    call_log.call_status = 'ringing'
                elif status == 'answered':
                    call_log.call_status = 'answered'
                    call_log.call_answered = datetime.utcnow()
                elif status == 'completed':
                    call_log.call_status = 'completed'
                    call_log.call_end = datetime.utcnow()
                    if duration:
                        call_log.call_duration = int(duration)
                elif status == 'busy':
                    call_log.call_status = 'busy'
                    call_log.call_end = datetime.utcnow()
                elif status == 'no-answer':
                    call_log.call_status = 'no-answer'
                    call_log.call_end = datetime.utcnow()
                elif status == 'failed':
                    call_log.call_status = 'failed'
                    call_log.call_end = datetime.utcnow()
                elif status == 'canceled':
                    call_log.call_status = 'canceled'
                    call_log.call_end = datetime.utcnow()
                
                await db.commit()
                
                # Update campaign metrics
                await self._update_campaign_metrics(call_log.campaign_id)
                
                logger.info(f"Call {call_log.twilio_call_sid} status updated to {status}")
                
        except Exception as e:
            logger.error(f"Error handling call status webhook: {e}")
    
    async def transfer_call(self, call_log_id: int, transfer_number: str) -> Dict[str, Any]:
        """Transfer call to human agent with AI disconnect detection"""
        try:
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if not call_log or not call_log.twilio_call_sid:
                    raise ValueError(f"Call log {call_log_id} not found or no Twilio SID")
                
                # Create enhanced transfer TwiML with human detection
                twiml = VoiceResponse()
                
                # Bridge the call to human agent with monitoring
                dial = twiml.dial(
                    transfer_number,
                    timeout=30,
                    # Webhook to detect when human agent answers
                    action=f"https://{settings.DOMAIN}/webhooks/twilio/transfer-status/{call_log_id}",
                    method="POST"
                )
                
                # Conference-based transfer for better control
                conference_name = f"transfer-{call_log_id}-{datetime.utcnow().timestamp()}"
                
                # Create conference room
                dial.conference(
                    conference_name,
                    # Monitor human agent connection
                    statusCallback=f"https://{settings.DOMAIN}/webhooks/twilio/conference-status/{call_log_id}",
                    statusCallbackMethod="POST",
                    statusCallbackEvent="start,end,join,leave,mute,unmute,hold,unhold",
                    # AI detection settings
                    eventCallbackUrl=f"https://{settings.DOMAIN}/webhooks/twilio/conference-events/{call_log_id}",
                    beep=False,
                    waitUrl="",
                    maxParticipants=3  # Prospect, AI, Human agent
                )
                
                # Update the call with new TwiML
                call = self.client.calls(call_log.twilio_call_sid).update(
                    twiml=str(twiml)
                )
                
                # Update call log
                call_log.transfer_attempted = True
                call_log.transfer_number = transfer_number
                call_log.transfer_time = datetime.utcnow()
                call_log.status = CallStatus.TRANSFERRING
                await db.commit()
                
                # Start monitoring for human agent connection
                await self._monitor_transfer_progress(call_log_id, conference_name)
                
                logger.info(f"Call {call_log.twilio_call_sid} transferred to {transfer_number} via conference {conference_name}")
                
                return {
                    'call_sid': call_log.twilio_call_sid,
                    'transfer_number': transfer_number,
                    'conference_name': conference_name,
                    'status': 'transferring'
                }
                
        except Exception as e:
            logger.error(f"Error transferring call: {e}")
            raise
    
    async def _monitor_transfer_progress(self, call_log_id: int, conference_name: str):
        """Monitor transfer progress and detect human agent connection"""
        try:
            # Start background monitoring task
            asyncio.create_task(self._transfer_monitoring_loop(call_log_id, conference_name))
            
        except Exception as e:
            logger.error(f"Error starting transfer monitoring: {e}")
    
    async def _transfer_monitoring_loop(self, call_log_id: int, conference_name: str):
        """Background loop to monitor transfer and detect human agent"""
        try:
            max_wait_time = 60  # 60 seconds max wait
            check_interval = 2  # Check every 2 seconds
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                # Check conference status
                transfer_status = await self._check_transfer_status(call_log_id, conference_name)
                
                if transfer_status == 'human_connected':
                    # Human agent answered - disconnect AI
                    await self._disconnect_ai_from_call(call_log_id)
                    logger.info(f"Human agent connected to call {call_log_id}, AI disconnected")
                    break
                    
                elif transfer_status == 'failed':
                    # Transfer failed - resume AI conversation
                    await self._resume_ai_conversation(call_log_id)
                    logger.info(f"Transfer failed for call {call_log_id}, AI resumed")
                    break
                    
                elif transfer_status == 'no_answer':
                    # No answer from human - resume AI or end call
                    await self._handle_transfer_no_answer(call_log_id)
                    break
                
                await asyncio.sleep(check_interval)
                elapsed_time += check_interval
            
            # Timeout reached
            if elapsed_time >= max_wait_time:
                logger.warning(f"Transfer monitoring timeout for call {call_log_id}")
                await self._handle_transfer_timeout(call_log_id)
                
        except Exception as e:
            logger.error(f"Error in transfer monitoring loop: {e}")
    
    async def _check_transfer_status(self, call_log_id: int, conference_name: str) -> str:
        """Check current transfer status"""
        try:
            # Get conference details
            conferences = self.client.conferences.list(friendly_name=conference_name)
            
            if not conferences:
                return 'no_conference'
            
            conference = conferences[0]
            participants = self.client.conferences(conference.sid).participants.list()
            
            # Analyze participants
            human_agent_connected = False
            prospect_connected = False
            
            for participant in participants:
                # Check if this is the human agent (outbound call to transfer number)
                if participant.call_sid_to_coach is None:  # Not coaching, actual participant
                    if participant.muted == False and participant.hold == False:
                        # Active participant - could be human agent
                        if self._is_human_agent_call(participant, call_log_id):
                            human_agent_connected = True
                        else:
                            prospect_connected = True
            
            # Determine status
            if human_agent_connected and prospect_connected:
                return 'human_connected'
            elif not human_agent_connected and prospect_connected:
                return 'waiting_for_human'
            else:
                return 'failed'
                
        except Exception as e:
            logger.error(f"Error checking transfer status: {e}")
            return 'error'
    
    async def _is_human_agent_call(self, participant, call_log_id: int) -> bool:
        """Determine if participant is the human agent"""
        try:
            # Get call details
            call = self.client.calls(participant.call_sid).fetch()
            
            # Check if call is to transfer number
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if call_log and call_log.transfer_number:
                    # Check if this call is to the transfer number
                    return call.to == call_log.transfer_number
                    
        except Exception as e:
            logger.error(f"Error checking if human agent call: {e}")
            
        return False
    
    async def _disconnect_ai_from_call(self, call_log_id: int):
        """Disconnect AI from call when human agent connects"""
        try:
            # End AI conversation
            from app.services.ai_conversation import ai_conversation_engine
            await ai_conversation_engine.end_conversation(call_log_id)
            
            # Close media stream
            from app.services.media_stream_handler import media_stream_handler
            await media_stream_handler.close_stream(call_log_id)
            
            # Update call log
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if call_log:
                    call_log.status = CallStatus.TRANSFERRED
                    call_log.ai_disconnected_at = datetime.utcnow()
                    await db.commit()
            
            # Notify call orchestration to free up capacity
            from app.services.call_orchestration import call_orchestration_service
            await call_orchestration_service.handle_ai_disconnect(call_log_id)
            
            logger.info(f"AI successfully disconnected from call {call_log_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting AI from call: {e}")
    
    async def _resume_ai_conversation(self, call_log_id: int):
        """Resume AI conversation if transfer fails"""
        try:
            # Update call status
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if call_log:
                    call_log.status = CallStatus.IN_PROGRESS
                    call_log.transfer_failed = True
                    await db.commit()
            
            # Create fallback TwiML to resume AI
            twiml = VoiceResponse()
            twiml.say("I'm sorry, our specialist is currently unavailable. Let me continue helping you.")
            
            # Reconnect to AI media stream
            twiml.start().stream(
                url=f"wss://{settings.DOMAIN}/ws/media-stream/{call_log_id}",
                track="both_tracks"
            )
            
            # Update call with resume TwiML
            call = self.client.calls(call_log.twilio_call_sid).update(
                twiml=str(twiml)
            )
            
            # Restart AI conversation
            from app.services.ai_conversation import ai_conversation_engine
            await ai_conversation_engine.resume_conversation(call_log_id)
            
            logger.info(f"AI conversation resumed for call {call_log_id}")
            
        except Exception as e:
            logger.error(f"Error resuming AI conversation: {e}")
    
    async def _handle_transfer_no_answer(self, call_log_id: int):
        """Handle case when human agent doesn't answer"""
        try:
            # Update call log
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if call_log:
                    call_log.transfer_failed = True
                    call_log.transfer_failure_reason = "no_answer"
                    await db.commit()
            
            # Option 1: Try backup transfer number
            await self._try_backup_transfer(call_log_id)
            
            # Option 2: If no backup, politely end call
            # await self._politely_end_call(call_log_id)
            
        except Exception as e:
            logger.error(f"Error handling transfer no answer: {e}")
    
    async def _try_backup_transfer(self, call_log_id: int):
        """Try backup transfer number if primary fails"""
        try:
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if call_log:
                    campaign_query = select(Campaign).where(Campaign.id == call_log.campaign_id)
                    campaign = await db.execute(campaign_query)
                    campaign = campaign.scalar_one_or_none()
                    
                    if campaign and campaign.backup_transfer_number:
                        logger.info(f"Trying backup transfer for call {call_log_id}")
                        await self.transfer_call(call_log_id, campaign.backup_transfer_number)
                    else:
                        # No backup - resume AI or end call
                        await self._resume_ai_conversation(call_log_id)
                        
        except Exception as e:
            logger.error(f"Error trying backup transfer: {e}")
    
    async def _handle_transfer_timeout(self, call_log_id: int):
        """Handle transfer monitoring timeout"""
        try:
            logger.warning(f"Transfer timeout for call {call_log_id}")
            
            # Update call log
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if call_log:
                    call_log.transfer_failed = True
                    call_log.transfer_failure_reason = "timeout"
                    await db.commit()
            
            # Default to AI disconnect (assume human connected)
            await self._disconnect_ai_from_call(call_log_id)
            
        except Exception as e:
            logger.error(f"Error handling transfer timeout: {e}")
    
    async def hangup_call(self, call_log_id: int) -> Dict[str, Any]:
        """Hang up an active call"""
        try:
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if not call_log or not call_log.twilio_call_sid:
                    raise ValueError(f"Call log {call_log_id} not found or no Twilio SID")
                
                # Hang up the call
                call = self.client.calls(call_log.twilio_call_sid).update(
                    status='completed'
                )
                
                # Update call log
                call_log.call_status = 'completed'
                call_log.call_end = datetime.utcnow()
                await db.commit()
                
                logger.info(f"Call {call_log.twilio_call_sid} hung up")
                
                return {
                    'call_sid': call_log.twilio_call_sid,
                    'status': 'hung_up'
                }
                
        except Exception as e:
            logger.error(f"Error hanging up call: {e}")
            raise
    
    async def get_call_recordings(self, call_log_id: int) -> List[Dict[str, Any]]:
        """Get recordings for a call"""
        try:
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if not call_log or not call_log.twilio_call_sid:
                    raise ValueError(f"Call log {call_log_id} not found or no Twilio SID")
                
                recordings = self.client.recordings.list(call_sid=call_log.twilio_call_sid)
                
                recording_data = []
                for recording in recordings:
                    recording_data.append({
                        'recording_sid': recording.sid,
                        'duration': recording.duration,
                        'date_created': recording.date_created,
                        'uri': recording.uri,
                        'download_url': f"https://api.twilio.com{recording.uri.replace('.json', '.mp3')}"
                    })
                
                return recording_data
                
        except Exception as e:
            logger.error(f"Error getting call recordings: {e}")
            raise
    
    async def _update_campaign_metrics(self, campaign_id: int) -> None:
        """Update campaign metrics after call status change"""
        try:
            async with get_db() as db:
                # Get campaign stats
                from sqlalchemy import func
                
                stats_query = select(
                    func.count(CallLog.id).label('total_calls'),
                    func.sum(func.case([(CallLog.call_status == 'answered', 1)], else_=0)).label('answered_calls'),
                    func.sum(func.case([(CallLog.transfer_attempted == True, 1)], else_=0)).label('transfers'),
                    func.sum(func.case([(CallLog.call_status == 'completed', CallLog.call_duration)], else_=0)).label('total_duration')
                ).where(CallLog.campaign_id == campaign_id)
                
                stats = await db.execute(stats_query)
                stats = stats.first()
                
                if stats and stats.total_calls > 0:
                    answer_rate = (stats.answered_calls or 0) / stats.total_calls * 100
                    transfer_rate = (stats.transfers or 0) / stats.total_calls * 100
                    avg_duration = (stats.total_duration or 0) / stats.total_calls
                    
                    # Update campaign metrics
                    campaign_update = update(Campaign).where(Campaign.id == campaign_id).values(
                        answer_rate=answer_rate,
                        transfer_rate=transfer_rate,
                        avg_call_duration=avg_duration,
                        total_calls=stats.total_calls,
                        answered_calls=stats.answered_calls or 0,
                        transfers=stats.transfers or 0,
                        updated_at=datetime.utcnow()
                    )
                    await db.execute(campaign_update)
                    await db.commit()
                
        except Exception as e:
            logger.error(f"Error updating campaign metrics: {e}")
    
    async def get_active_calls(self, campaign_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of active calls"""
        try:
            async with get_db() as db:
                query = select(CallLog).where(
                    CallLog.call_status.in_(['initiated', 'ringing', 'answered'])
                )
                
                if campaign_id:
                    query = query.where(CallLog.campaign_id == campaign_id)
                
                result = await db.execute(query)
                call_logs = result.scalars().all()
                
                active_calls = []
                for call_log in call_logs:
                    # Get current call status from Twilio
                    try:
                        if call_log.twilio_call_sid:
                            call = self.client.calls(call_log.twilio_call_sid).fetch()
                            current_status = call.status
                        else:
                            current_status = call_log.call_status
                    except:
                        current_status = call_log.call_status
                    
                    active_calls.append({
                        'call_log_id': call_log.id,
                        'twilio_call_sid': call_log.twilio_call_sid,
                        'campaign_id': call_log.campaign_id,
                        'lead_id': call_log.lead_id,
                        'phone_number': call_log.phone_number,
                        'status': current_status,
                        'call_start': call_log.call_start,
                        'call_duration': call_log.call_duration
                    })
                
                return active_calls
                
        except Exception as e:
            logger.error(f"Error getting active calls: {e}")
            return []

# Global instance
twilio_service = TwilioIntegrationService() 