import logging
import asyncio
import json
import base64
from typing import Dict, Any
from datetime import datetime
from websockets.exceptions import ConnectionClosed
import io
import boto3
from botocore.exceptions import ClientError

from app.services.ai_conversation import ai_conversation_engine
from app.services.aws_connect_integration import aws_connect_service
from app.config import settings
from app.database import get_db
from app.models import CallLog

logger = logging.getLogger(__name__)


class AWSConnectMediaHandler:
    def __init__(self):
        self.active_streams: Dict[int, Dict[str, Any]] = {}
        self.audio_buffers: Dict[int, io.BytesIO] = {}
        self.kinesis_video_client = boto3.client(
            'kinesisvideo',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )

    async def handle_connect_media_stream(self, websocket, path: str):
        """Handle incoming WebSocket media stream from Amazon Connect"""
        try:
            # Extract call_log_id from path
            call_log_id = int(path.split('/')[-1])

            logger.info(
                f"New Amazon Connect media stream connection for call {call_log_id}")

            # Initialize stream data
            self.active_streams[call_log_id] = {
                'websocket': websocket,
                'contact_id': None,
                'started': datetime.utcnow(),
                'audio_buffer': io.BytesIO(),
                'stream_arn': None
            }

            # Start AI conversation
            conversation_context = await ai_conversation_engine.start_conversation(call_log_id)

            # Send initial greeting
            await self._send_initial_greeting(call_log_id, conversation_context)

            # Handle incoming messages
            async for message in websocket:
                await self._process_connect_media_message(call_log_id, message)

        except ConnectionClosed:
            logger.info(
                f"Amazon Connect media stream connection closed for call {call_log_id}")
        except Exception as e:
            logger.error(f"Error handling Amazon Connect media stream: {e}")
        finally:
            # Clean up stream
            if call_log_id in self.active_streams:
                del self.active_streams[call_log_id]
            if call_log_id in self.audio_buffers:
                del self.audio_buffers[call_log_id]

    async def _process_connect_media_message(
            self, call_log_id: int, message: str):
        """Process incoming media message from Amazon Connect"""
        try:
            data = json.loads(message)
            event_type = data.get('eventType')

            if event_type == 'start':
                await self._handle_stream_start(call_log_id, data)
            elif event_type == 'media':
                await self._handle_media_data(call_log_id, data)
            elif event_type == 'stop':
                await self._handle_stream_stop(call_log_id, data)
            elif event_type == 'connected':
                await self._handle_stream_connected(call_log_id, data)
            else:
                logger.debug(f"Unknown event type: {event_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in media message: {message}")
        except Exception as e:
            logger.error(f"Error processing media message: {e}")

    async def _handle_stream_start(
            self, call_log_id: int, data: Dict[str, Any]):
        """Handle stream start event"""
        try:
            if call_log_id not in self.active_streams:
                return

            stream_info = self.active_streams[call_log_id]

            # Extract stream information
            stream_info['contact_id'] = data.get('contactId')
            stream_info['stream_arn'] = data.get('streamARN')

            # Create Kinesis Video Stream for recording (if enabled)
            async with get_db() as db:
                from sqlalchemy import select
                call_log_query = select(CallLog).where(
                    CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()

                if call_log:
                    from app.models import Campaign
                    campaign_query = select(Campaign).where(
                        Campaign.id == call_log.campaign_id)
                    campaign = await db.execute(campaign_query)
                    campaign = campaign.scalar_one_or_none()

                    if campaign and campaign.call_recording_enabled:
                        await self._setup_call_recording(call_log_id, stream_info['stream_arn'])

            logger.info(
                f"Stream started for call {call_log_id}, contact {stream_info['contact_id']}")

        except Exception as e:
            logger.error(f"Error handling stream start: {e}")

    async def _handle_media_data(self, call_log_id: int, data: Dict[str, Any]):
        """Handle incoming audio data from Amazon Connect"""
        try:
            if call_log_id not in self.active_streams:
                return

            # Extract audio payload
            payload = data.get('payload', {})
            audio_data = payload.get('audioEventData', {})

            if 'audioChunk' in audio_data:
                # Decode base64 audio chunk
                audio_chunk = base64.b64decode(audio_data['audioChunk'])

                # Add to audio buffer
                if call_log_id not in self.audio_buffers:
                    self.audio_buffers[call_log_id] = io.BytesIO()

                self.audio_buffers[call_log_id].write(audio_chunk)

                # Process audio chunk for AI conversation
                await self._process_audio_chunk(call_log_id, audio_chunk)

        except Exception as e:
            logger.error(f"Error handling media data: {e}")

    async def _handle_stream_stop(
            self, call_log_id: int, data: Dict[str, Any]):
        """Handle stream stop event"""
        try:
            logger.info(f"Stream stopped for call {call_log_id}")

            # End AI conversation
            await ai_conversation_engine.end_conversation(call_log_id)

            # Clean up resources
            if call_log_id in self.active_streams:
                del self.active_streams[call_log_id]
            if call_log_id in self.audio_buffers:
                del self.audio_buffers[call_log_id]

        except Exception as e:
            logger.error(f"Error handling stream stop: {e}")

    async def _handle_stream_connected(
            self, call_log_id: int, data: Dict[str, Any]):
        """Handle stream connected event"""
        try:
            logger.info(f"Stream connected for call {call_log_id}")

            # Update call log status
            async with get_db() as db:
                from sqlalchemy import select
                call_log_query = select(CallLog).where(
                    CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()

                if call_log:
                    call_log.call_status = 'connected'
                    await db.commit()

        except Exception as e:
            logger.error(f"Error handling stream connected: {e}")

    async def _send_initial_greeting(
            self, call_log_id: int, conversation_context: Dict[str, Any]):
        """Send initial AI greeting through Amazon Connect"""
        try:
            # Generate greeting text
            greeting_text = conversation_context.get(
                'greeting', 'Hello, thank you for your time.')

            # Convert to audio using ElevenLabs
            audio_bytes = await ai_conversation_engine._text_to_speech(greeting_text)

            if audio_bytes:
                await self._send_audio_to_connect(call_log_id, audio_bytes)

        except Exception as e:
            logger.error(f"Error sending initial greeting: {e}")

    async def _send_audio_to_connect(
            self, call_log_id: int, audio_bytes: bytes):
        """Send audio data to Amazon Connect stream"""
        try:
            if call_log_id not in self.active_streams:
                return

            stream_info = self.active_streams[call_log_id]
            websocket = stream_info['websocket']

            # Encode audio as base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

            # Create media message for Amazon Connect
            media_message = {
                'eventType': 'media',
                'payload': {
                    'audioEventData': {
                        'audioChunk': audio_base64
                    }
                }
            }

            # Send through WebSocket
            await websocket.send(json.dumps(media_message))

        except Exception as e:
            logger.error(f"Error sending audio to Connect: {e}")

    async def _process_audio_chunk(self, call_log_id: int, audio_chunk: bytes):
        """Process audio chunk for AI conversation"""
        try:
            # Buffer audio for speech detection
            buffer_size = 8000  # 1 second at 8kHz

            if call_log_id not in self.audio_buffers:
                self.audio_buffers[call_log_id] = io.BytesIO()

            buffer = self.audio_buffers[call_log_id]
            buffer.write(audio_chunk)

            # Check if we have enough audio for processing
            if buffer.tell() >= buffer_size:
                # Reset buffer position
                buffer.seek(0)
                audio_data = buffer.read()
                buffer.seek(0)
                buffer.truncate()

                # Process with AI conversation engine
                await self._process_with_ai(call_log_id, audio_data)

        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")

    async def _process_with_ai(self, call_log_id: int, audio_data: bytes):
        """Process audio data with AI conversation engine"""
        try:
            # Convert audio to text using Deepgram
            transcript = await ai_conversation_engine._speech_to_text(audio_data)

            if transcript and transcript.strip():
                logger.info(f"Customer said: {transcript}")

                # Generate AI response
                ai_response = await ai_conversation_engine.process_customer_input(
                    call_log_id, transcript
                )

                if ai_response:
                    response_text = ai_response.get('text', '')
                    action = ai_response.get('action', 'speak')

                    if action == 'speak' and response_text:
                        # Convert response to audio
                        audio_bytes = await ai_conversation_engine._text_to_speech(response_text)

                        if audio_bytes:
                            await self._send_audio_to_connect(call_log_id, audio_bytes)

                    elif action == 'transfer':
                        # Initiate transfer
                        await self._initiate_transfer(call_log_id)

        except Exception as e:
            logger.error(f"Error processing with AI: {e}")

    async def _initiate_transfer(self, call_log_id: int):
        """Initiate call transfer to human agent"""
        try:
            # Get campaign transfer settings
            async with get_db() as db:
                from sqlalchemy import select
                call_log_query = select(CallLog).where(
                    CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()

                if not call_log:
                    return

                from app.models import Campaign
                campaign_query = select(Campaign).where(
                    Campaign.id == call_log.campaign_id)
                campaign = await db.execute(campaign_query)
                campaign = campaign.scalar_one_or_none()

                if not campaign or not campaign.transfer_number:
                    logger.warning(
                        f"No transfer number configured for campaign {call_log.campaign_id}")
                    return

                # Send transfer message
                transfer_message = "Great! Let me connect you with one of our specialists who can help you further. Please hold for just a moment."
                audio_bytes = await ai_conversation_engine._text_to_speech(transfer_message)

                if audio_bytes:
                    await self._send_audio_to_connect(call_log_id, audio_bytes)

                # Wait a moment for message to play
                await asyncio.sleep(3)

                # Initiate transfer via AWS Connect
                await aws_connect_service.transfer_call(call_log_id, campaign.transfer_number)

                logger.info(
                    f"Initiated transfer for call {call_log_id} to {campaign.transfer_number}")

        except Exception as e:
            logger.error(f"Error initiating transfer: {e}")

    async def _setup_call_recording(self, call_log_id: int, stream_arn: str):
        """Setup call recording using Kinesis Video Streams"""
        try:
            # Create a Kinesis Video Stream for recording
            stream_name = f"call-recording-{call_log_id}"

            try:
                response = self.kinesis_video_client.create_stream(
                    StreamName=stream_name,
                    DataRetentionInHours=24 * 7,  # 7 days retention
                    MediaType='audio/L16; rate=8000; channels=1'
                )

                logger.info(
                    f"Created Kinesis Video Stream for call {call_log_id}: {stream_name}")

                # Update call log with recording information
                async with get_db() as db:
                    from sqlalchemy import select
                    call_log_query = select(CallLog).where(
                        CallLog.id == call_log_id)
                    call_log = await db.execute(call_log_query)
                    call_log = call_log.scalar_one_or_none()

                    if call_log:
                        call_log.recording_url = response['StreamARN']
                        await db.commit()

            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceInUseException':
                    logger.info(
                        f"Kinesis Video Stream already exists: {stream_name}")
                else:
                    logger.error(f"Error creating Kinesis Video Stream: {e}")

        except Exception as e:
            logger.error(f"Error setting up call recording: {e}")

    async def close_stream(self, call_log_id: int):
        """Close media stream for a call"""
        try:
            if call_log_id in self.active_streams:
                stream_info = self.active_streams[call_log_id]
                websocket = stream_info['websocket']

                # Send close message
                close_message = {
                    'eventType': 'stop',
                    'payload': {}
                }

                await websocket.send(json.dumps(close_message))

                # Clean up
                del self.active_streams[call_log_id]

            if call_log_id in self.audio_buffers:
                del self.audio_buffers[call_log_id]

            logger.info(f"Closed media stream for call {call_log_id}")

        except Exception as e:
            logger.error(f"Error closing stream: {e}")


# Global instance
aws_connect_media_handler = AWSConnectMediaHandler()
