import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import asyncio
import boto3
from botocore.exceptions import ClientError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from app.config import settings
from app.database import get_db
from app.models import Campaign, Lead, CallLog, DIDPool

logger = logging.getLogger(__name__)

class AWSConnectIntegrationService:
    def __init__(self):
        self.connect_client = boto3.client(
            'connect',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        self.base_url = settings.base_url
        
    async def initiate_call(self, lead_id: int, campaign_id: int, did_id: int) -> Dict[str, Any]:
        """Initiate an outbound call with AI conversation flow using Amazon Connect"""
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
                
                # Prepare contact attributes for Amazon Connect
                contact_attributes = {
                    'CallLogId': str(call_log.id),
                    'CampaignId': str(campaign_id),
                    'LeadId': str(lead_id),
                    'DIDId': str(did_id),
                    'AIEnabled': 'true',
                    'GreetingPrompt': campaign.greeting_prompt or "Hello, thank you for your time.",
                    'MediaStreamUrl': f"wss://{settings.domain}/ws/connect-media-stream/{call_log.id}"
                }
                
                # Initiate outbound call using Amazon Connect
                response = self.connect_client.start_outbound_voice_contact(
                    DestinationPhoneNumber=lead.phone_number,
                    ContactFlowId=settings.aws_connect_contact_flow_id,
                    InstanceId=settings.aws_connect_instance_id,
                    SourcePhoneNumber=did.phone_number,
                    QueueId=settings.aws_connect_queue_id,
                    Attributes=contact_attributes
                )
                
                # Update call log with Amazon Connect contact ID
                call_log.aws_contact_id = response['ContactId']
                await db.commit()
                
                logger.info(f"Call initiated: {response['ContactId']} to {lead.phone_number}")
                
                return {
                    'contact_id': response['ContactId'],
                    'call_log_id': call_log.id,
                    'status': 'initiated',
                    'to_number': lead.phone_number,
                    'from_number': did.phone_number
                }
                
        except ClientError as e:
            logger.error(f"AWS Connect error initiating call: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initiating call: {e}")
            raise
    
    async def handle_contact_event(self, event_data: Dict[str, Any]) -> None:
        """Handle Amazon Connect contact events (replaces Twilio webhooks)"""
        try:
            contact_id = event_data.get('ContactId')
            event_type = event_data.get('EventType')
            
            if not contact_id:
                logger.warning("No ContactId in event data")
                return
                
            async with get_db() as db:
                # Find call log by contact ID
                call_log_query = select(CallLog).where(CallLog.aws_contact_id == contact_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if not call_log:
                    logger.warning(f"Call log not found for contact {contact_id}")
                    return
                
                # Update call log based on event type
                if event_type == 'CONTACT_FLOW_STARTED':
                    call_log.call_status = 'ringing'
                elif event_type == 'CONTACT_CONNECTED':
                    call_log.call_status = 'answered'
                    call_log.call_answered = datetime.utcnow()
                elif event_type == 'CONTACT_DISCONNECTED':
                    call_log.call_status = 'completed'
                    call_log.call_end = datetime.utcnow()
                    
                    # Calculate duration if we have both start and end times
                    if call_log.call_answered and call_log.call_end:
                        duration = (call_log.call_end - call_log.call_answered).total_seconds()
                        call_log.call_duration = int(duration)
                        
                elif event_type == 'CONTACT_TRANSFERRED':
                    call_log.call_status = 'transferred'
                    call_log.transfer_attempted = True
                    call_log.transfer_time = datetime.utcnow()
                elif event_type == 'CONTACT_QUEUED':
                    call_log.call_status = 'queued'
                
                await db.commit()
                
                # Update campaign metrics
                await self._update_campaign_metrics(call_log.campaign_id)
                
                logger.info(f"Contact {contact_id} status updated to {call_log.call_status}")
                
        except Exception as e:
            logger.error(f"Error handling contact event: {e}")
    
    async def transfer_call(self, call_log_id: int, transfer_number: str) -> Dict[str, Any]:
        """Transfer call to human agent using Amazon Connect"""
        try:
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if not call_log or not call_log.aws_contact_id:
                    raise ValueError(f"Call log {call_log_id} not found or no AWS contact ID")
                
                # Use Amazon Connect's transfer functionality
                response = self.connect_client.transfer_contact(
                    InstanceId=settings.aws_connect_instance_id,
                    ContactId=call_log.aws_contact_id,
                    QueueId=settings.aws_connect_queue_id,
                    UserId=None,  # Will be set based on transfer queue logic
                    ContactFlowId=settings.aws_connect_contact_flow_id
                )
                
                # Update call log
                call_log.transfer_attempted = True
                call_log.transfer_number = transfer_number
                call_log.transfer_time = datetime.utcnow()
                call_log.call_status = 'transferring'
                await db.commit()
                
                logger.info(f"Call {call_log.aws_contact_id} transferred to {transfer_number}")
                
                return {
                    'contact_id': call_log.aws_contact_id,
                    'transfer_number': transfer_number,
                    'status': 'transferring'
                }
                
        except ClientError as e:
            logger.error(f"AWS Connect error transferring call: {e}")
            raise
        except Exception as e:
            logger.error(f"Error transferring call: {e}")
            raise
    
    async def hangup_call(self, call_log_id: int) -> Dict[str, Any]:
        """Hang up an active call using Amazon Connect"""
        try:
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if not call_log or not call_log.aws_contact_id:
                    raise ValueError(f"Call log {call_log_id} not found or no AWS contact ID")
                
                # Disconnect contact using Amazon Connect
                response = self.connect_client.stop_contact(
                    ContactId=call_log.aws_contact_id,
                    InstanceId=settings.aws_connect_instance_id
                )
                
                # Update call log
                call_log.call_status = 'completed'
                call_log.call_end = datetime.utcnow()
                await db.commit()
                
                logger.info(f"Call {call_log.aws_contact_id} hung up")
                
                return {
                    'contact_id': call_log.aws_contact_id,
                    'status': 'hung_up'
                }
                
        except ClientError as e:
            logger.error(f"AWS Connect error hanging up call: {e}")
            raise
        except Exception as e:
            logger.error(f"Error hanging up call: {e}")
            raise
    
    async def get_call_recordings(self, call_log_id: int) -> List[Dict[str, Any]]:
        """Get call recordings from Amazon Connect"""
        try:
            async with get_db() as db:
                call_log_query = select(CallLog).where(CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()
                
                if not call_log or not call_log.aws_contact_id:
                    return []
                
                # Get contact details including recordings
                response = self.connect_client.describe_contact(
                    InstanceId=settings.aws_connect_instance_id,
                    ContactId=call_log.aws_contact_id
                )
                
                recordings = []
                contact = response.get('Contact', {})
                
                # Check if recording is available
                if contact.get('RecordingConfiguration', {}).get('RecordingId'):
                    recording_id = contact['RecordingConfiguration']['RecordingId']
                    
                    # Get recording URL
                    try:
                        recording_response = self.connect_client.get_contact_recording(
                            InstanceId=settings.aws_connect_instance_id,
                            ContactId=call_log.aws_contact_id,
                            RecordingId=recording_id
                        )
                        
                        recordings.append({
                            'recording_id': recording_id,
                            'recording_url': recording_response.get('RecordingUrl'),
                            'duration': contact.get('LastUpdateTimestamp', 0),
                            'format': 'wav'
                        })
                    except ClientError as e:
                        logger.warning(f"Could not get recording for contact {call_log.aws_contact_id}: {e}")
                
                return recordings
                
        except ClientError as e:
            logger.error(f"AWS Connect error getting recordings: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting call recordings: {e}")
            return []
    
    async def get_active_calls(self, campaign_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get active calls from Amazon Connect"""
        try:
            # Get active contacts from Amazon Connect
            response = self.connect_client.get_current_metric_data(
                InstanceId=settings.aws_connect_instance_id,
                Filters={
                    'Queues': [settings.aws_connect_queue_id],
                    'Channels': ['VOICE']
                },
                CurrentMetrics=[
                    {'Name': 'AGENTS_ONLINE', 'Unit': 'COUNT'},
                    {'Name': 'CONTACTS_IN_QUEUE', 'Unit': 'COUNT'},
                    {'Name': 'CONTACTS_HANDLED', 'Unit': 'COUNT'}
                ]
            )
            
            active_calls = []
            
            # Get call logs for active calls
            async with get_db() as db:
                query = select(CallLog).where(
                    CallLog.call_status.in_(['initiated', 'ringing', 'answered', 'in_progress'])
                )
                
                if campaign_id:
                    query = query.where(CallLog.campaign_id == campaign_id)
                
                result = await db.execute(query)
                call_logs = result.scalars().all()
                
                for call_log in call_logs:
                    active_calls.append({
                        'call_log_id': call_log.id,
                        'contact_id': call_log.aws_contact_id,
                        'phone_number': call_log.phone_number,
                        'status': call_log.call_status,
                        'duration': (datetime.utcnow() - call_log.call_start).total_seconds(),
                        'campaign_id': call_log.campaign_id
                    })
            
            return active_calls
            
        except ClientError as e:
            logger.error(f"AWS Connect error getting active calls: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting active calls: {e}")
            return []
    
    async def _update_campaign_metrics(self, campaign_id: int) -> None:
        """Update campaign metrics based on call outcomes"""
        try:
            async with get_db() as db:
                # Get call statistics for the campaign
                from sqlalchemy import func
                
                stats_query = select(
                    func.count(CallLog.id).label('total_calls'),
                    func.count(CallLog.id).filter(CallLog.call_status == 'completed').label('completed_calls'),
                    func.count(CallLog.id).filter(CallLog.call_status == 'answered').label('answered_calls'),
                    func.avg(CallLog.call_duration).label('avg_duration')
                ).where(CallLog.campaign_id == campaign_id)
                
                result = await db.execute(stats_query)
                stats = result.first()
                
                if stats:
                    # Update campaign with latest metrics
                    campaign_query = select(Campaign).where(Campaign.id == campaign_id)
                    campaign = await db.execute(campaign_query)
                    campaign = campaign.scalar_one_or_none()
                    
                    if campaign:
                        campaign.total_calls = stats.total_calls or 0
                        campaign.completed_calls = stats.completed_calls or 0
                        campaign.answer_rate = (stats.answered_calls / stats.total_calls * 100) if stats.total_calls > 0 else 0
                        campaign.avg_call_duration = stats.avg_duration or 0
                        
                        await db.commit()
                        
        except Exception as e:
            logger.error(f"Error updating campaign metrics: {e}")
    
    async def create_contact_flow(self, campaign_id: int) -> str:
        """Create a contact flow for AI-powered conversations"""
        try:
            async with get_db() as db:
                campaign_query = select(Campaign).where(Campaign.id == campaign_id)
                campaign = await db.execute(campaign_query)
                campaign = campaign.scalar_one_or_none()
                
                if not campaign:
                    raise ValueError(f"Campaign {campaign_id} not found")
                
                # Create contact flow content for AI conversation
                contact_flow_content = {
                    "Version": "2019-10-30",
                    "StartAction": "12345678-1234-1234-1234-123456789012",
                    "Actions": [
                        {
                            "Identifier": "12345678-1234-1234-1234-123456789012",
                            "Type": "SetAttributes",
                            "Parameters": {
                                "Attributes": {
                                    "AIEnabled": "true",
                                    "CampaignId": str(campaign_id),
                                    "GreetingPrompt": campaign.greeting_prompt or "Hello, thank you for your time."
                                }
                            },
                            "Transitions": {
                                "NextAction": "12345678-1234-1234-1234-123456789013",
                                "Errors": [],
                                "Conditions": []
                            }
                        },
                        {
                            "Identifier": "12345678-1234-1234-1234-123456789013",
                            "Type": "StartMediaStreaming",
                            "Parameters": {
                                "MediaStreamTypes": ["Audio"],
                                "MediaStreamingStartCondition": "Immediate"
                            },
                            "Transitions": {
                                "NextAction": "12345678-1234-1234-1234-123456789014",
                                "Errors": [],
                                "Conditions": []
                            }
                        },
                        {
                            "Identifier": "12345678-1234-1234-1234-123456789014",
                            "Type": "Wait",
                            "Parameters": {
                                "TimeLimit": "300"
                            },
                            "Transitions": {
                                "NextAction": "12345678-1234-1234-1234-123456789015",
                                "Errors": [],
                                "Conditions": []
                            }
                        },
                        {
                            "Identifier": "12345678-1234-1234-1234-123456789015",
                            "Type": "Disconnect",
                            "Parameters": {},
                            "Transitions": {}
                        }
                    ]
                }
                
                # Create the contact flow
                response = self.connect_client.create_contact_flow(
                    InstanceId=settings.aws_connect_instance_id,
                    Name=f"AI_Campaign_{campaign_id}",
                    Type="CONTACT_FLOW",
                    Content=json.dumps(contact_flow_content),
                    Description=f"AI-powered contact flow for campaign {campaign_id}"
                )
                
                contact_flow_id = response['ContactFlowId']
                
                # Store contact flow ID in campaign
                campaign.aws_contact_flow_id = contact_flow_id
                await db.commit()
                
                logger.info(f"Created contact flow {contact_flow_id} for campaign {campaign_id}")
                
                return contact_flow_id
                
        except ClientError as e:
            logger.error(f"AWS Connect error creating contact flow: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating contact flow: {e}")
            raise

# Global instance
aws_connect_service = AWSConnectIntegrationService() 