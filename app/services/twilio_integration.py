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
from app.models import Campaign, Lead, CallLog, DIDPool, CallAnalytics

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
        """Transfer call to human agent"""
        try:
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if not call_log or not call_log.twilio_call_sid:
                    raise ValueError(f"Call log {call_log_id} not found or no Twilio SID")
                
                # Create transfer TwiML
                twiml = VoiceResponse()
                twiml.say("Please hold while I transfer you to a specialist.")
                twiml.dial(transfer_number, timeout=30)
                
                # Update the call with new TwiML
                call = self.client.calls(call_log.twilio_call_sid).update(
                    twiml=str(twiml)
                )
                
                # Update call log
                call_log.transfer_attempted = True
                call_log.transfer_number = transfer_number
                call_log.transfer_time = datetime.utcnow()
                await db.commit()
                
                logger.info(f"Call {call_log.twilio_call_sid} transferred to {transfer_number}")
                
                return {
                    'call_sid': call_log.twilio_call_sid,
                    'transfer_number': transfer_number,
                    'status': 'transferred'
                }
                
        except Exception as e:
            logger.error(f"Error transferring call: {e}")
            raise
    
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