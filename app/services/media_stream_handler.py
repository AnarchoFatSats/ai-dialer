import logging
import asyncio
import json
import base64
from typing import Dict, Any
from datetime import datetime
from websockets.exceptions import ConnectionClosed
import io

from app.services.ai_conversation import ai_conversation_engine
from app.services.aws_connect_integration import aws_connect_service
from app.database import get_db
from app.models import CallLog

logger = logging.getLogger(__name__)


class MediaStreamHandler:
    def __init__(self):
        self.active_streams: Dict[int, Dict[str, Any]] = {}
        self.audio_buffers: Dict[int, io.BytesIO] = {}

    async def handle_media_stream(self, websocket, path: str):
        """Handle incoming WebSocket media stream from AWS Connect"""
        try:
            # Extract call_log_id from path
            call_log_id = int(path.split('/')[-1])

            logger.info(f"New media stream connection for call {call_log_id}")

            # Initialize stream data
            self.active_streams[call_log_id] = {
                'websocket': websocket,
                'stream_sid': None,
                'call_sid': None,
                'started': datetime.utcnow(),
                'audio_buffer': io.BytesIO()
            }

            # Start AI conversation
            conversation_context = await ai_conversation_engine.start_conversation(call_log_id)

            # Send initial greeting
            await self._send_initial_greeting(call_log_id, conversation_context)

            # Handle incoming messages
            async for message in websocket:
                await self._process_media_message(call_log_id, message)

        except ConnectionClosed:
            logger.info(
                f"Media stream connection closed for call {call_log_id}")
        except Exception as e:
            logger.error(f"Error handling media stream: {e}")
        finally:
            # Clean up
            if call_log_id in self.active_streams:
                del self.active_streams[call_log_id]
            if call_log_id in self.audio_buffers:
                del self.audio_buffers[call_log_id]

            # End AI conversation
            await ai_conversation_engine.end_conversation(call_log_id)

    async def _process_media_message(self, call_log_id: int, message: str):
        """Process incoming media stream message"""
        try:
            data = json.loads(message)
            event = data.get('event')

            if event == 'connected':
                logger.info(f"Media stream connected for call {call_log_id}")

            elif event == 'start':
                # Store stream and call SIDs
                self.active_streams[call_log_id]['stream_sid'] = data.get(
                    'streamSid')
                self.active_streams[call_log_id]['call_sid'] = data.get(
                    'start', {}).get('callSid')
                logger.info(f"Media stream started for call {call_log_id}")

            elif event == 'media':
                # Process audio data
                await self._process_audio_data(call_log_id, data)

            elif event == 'stop':
                logger.info(f"Media stream stopped for call {call_log_id}")

        except Exception as e:
            logger.error(f"Error processing media message: {e}")

    async def _process_audio_data(
            self, call_log_id: int, media_data: Dict[str, Any]):
        """Process incoming audio data"""
        try:
            # Get audio payload
            payload = media_data.get('media', {}).get('payload', '')
            if not payload:
                return

            # Decode base64 audio
            audio_bytes = base64.b64decode(payload)

            # Buffer audio data
            if call_log_id not in self.audio_buffers:
                self.audio_buffers[call_log_id] = io.BytesIO()

            self.audio_buffers[call_log_id].write(audio_bytes)

            # Process audio in chunks (every 1 second of audio approximately)
            buffer_size = len(self.audio_buffers[call_log_id].getvalue())

            # Process when we have enough audio data (adjust based on sample
            # rate)
            if buffer_size >= 8000:  # Approximately 1 second of 8kHz mulaw audio
                await self._process_audio_chunk(call_log_id)

        except Exception as e:
            logger.error(f"Error processing audio data: {e}")

    async def _process_audio_chunk(self, call_log_id: int):
        """Process accumulated audio chunk"""
        try:
            if call_log_id not in self.audio_buffers:
                return

            # Get audio data
            audio_data = self.audio_buffers[call_log_id].getvalue()

            # Reset buffer
            self.audio_buffers[call_log_id] = io.BytesIO()

            # Process with AI conversation engine
            ai_response_audio = await ai_conversation_engine.process_audio_chunk(
                call_log_id, audio_data
            )

            # Send AI response back to call
            if ai_response_audio:
                await self._send_audio_response(call_log_id, ai_response_audio)

            # Check if call should be transferred
            should_transfer = await ai_conversation_engine.should_transfer_call(call_log_id)
            if should_transfer:
                await self._initiate_transfer(call_log_id)

        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")

    async def _send_audio_response(self, call_log_id: int, audio_bytes: bytes):
        """Send audio response back to the call"""
        try:
            if call_log_id not in self.active_streams:
                return

            stream_data = self.active_streams[call_log_id]
            websocket = stream_data['websocket']

            # Convert audio to base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

            # Create media message
            media_message = {
                'event': 'media',
                'streamSid': stream_data['stream_sid'],
                'media': {
                    'payload': audio_base64
                }
            }

            # Send to AWS Connect
            await websocket.send(json.dumps(media_message))

        except Exception as e:
            logger.error(f"Error sending audio response: {e}")

    async def _send_initial_greeting(
            self,
            call_log_id: int,
            conversation_context):
        """Send initial AI greeting"""
        try:
            if not conversation_context or not conversation_context.conversation_history:
                return

            # Get the initial greeting from conversation history
            initial_greeting = conversation_context.conversation_history[0]['content']

            # Convert to audio using AI conversation engine
            from app.services.ai_conversation import ai_conversation_engine
            audio_bytes = await ai_conversation_engine._text_to_speech(initial_greeting)

            # Send audio response
            if audio_bytes:
                await self._send_audio_response(call_log_id, audio_bytes)

        except Exception as e:
            logger.error(f"Error sending initial greeting: {e}")

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
                    await self._send_audio_response(call_log_id, audio_bytes)

                # Wait a moment for message to play
                await asyncio.sleep(3)

                # Initiate transfer via AWS Connect
                await aws_connect_service.transfer_call(call_log_id, campaign.transfer_number)

                logger.info(
                    f"Initiated transfer for call {call_log_id} to {campaign.transfer_number}")

        except Exception as e:
            logger.error(f"Error initiating transfer: {e}")

    async def _send_mark_message(self, call_log_id: int, mark_name: str):
        """Send mark message to AWS Connect"""
        try:
            if call_log_id not in self.active_streams:
                return

            stream_data = self.active_streams[call_log_id]
            websocket = stream_data['websocket']

            mark_message = {
                'event': 'mark',
                'streamSid': stream_data['stream_sid'],
                'mark': {
                    'name': mark_name
                }
            }

            await websocket.send(json.dumps(mark_message))

        except Exception as e:
            logger.error(f"Error sending mark message: {e}")

    async def clear_audio_buffer(self, call_log_id: int):
        """Clear audio buffer for a call"""
        try:
            # Send clear message to AWS Connect
            await self._send_clear_message(call_log_id)

            # Clear local buffer
            if call_log_id in self.audio_buffers:
                self.audio_buffers[call_log_id] = io.BytesIO()

        except Exception as e:
            logger.error(f"Error clearing audio buffer: {e}")

    async def _send_clear_message(self, call_log_id: int):
        """Send clear message to AWS Connect"""
        try:
            if call_log_id not in self.active_streams:
                return

            stream_data = self.active_streams[call_log_id]
            websocket = stream_data['websocket']

            clear_message = {
                'event': 'clear',
                'streamSid': stream_data['stream_sid']
            }

            await websocket.send(json.dumps(clear_message))

        except Exception as e:
            logger.error(f"Error sending clear message: {e}")

    def get_active_streams(self) -> Dict[int, Dict[str, Any]]:
        """Get list of active media streams"""
        return {
            call_log_id: {
                'stream_sid': stream_data['stream_sid'],
                'call_sid': stream_data['call_sid'],
                'started': stream_data['started'],
                'duration': (datetime.utcnow() - stream_data['started']).total_seconds()
            }
            for call_log_id, stream_data in self.active_streams.items()
        }

    async def close_stream(self, call_log_id: int):
        """Close media stream for a call"""
        try:
            if call_log_id in self.active_streams:
                stream_data = self.active_streams[call_log_id]
                websocket = stream_data['websocket']

                # Send stop message
                stop_message = {
                    'event': 'stop',
                    'streamSid': stream_data['stream_sid']
                }

                await websocket.send(json.dumps(stop_message))

                # Close websocket
                await websocket.close()

                # Clean up
                del self.active_streams[call_log_id]

            if call_log_id in self.audio_buffers:
                del self.audio_buffers[call_log_id]

            logger.info(f"Closed media stream for call {call_log_id}")

        except Exception as e:
            logger.error(f"Error closing stream: {e}")


# Global instance
media_stream_handler = MediaStreamHandler()
