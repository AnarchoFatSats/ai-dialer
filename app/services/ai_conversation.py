import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import anthropic
from deepgram import Deepgram
import elevenlabs
from sqlalchemy import select, update

from app.config import settings
from app.database import get_db
from app.models import Campaign, Lead, CallLog
from app.services.voicemail_detection import voicemail_detection_service, VoicemailState

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    GREETING = "greeting"
    QUALIFICATION = "qualification"
    PRESENTATION = "presentation"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"
    TRANSFER = "transfer"
    COMPLETED = "completed"


@dataclass
class ConversationContext:
    call_log_id: int
    campaign_id: int
    lead_id: int
    state: ConversationState
    conversation_history: List[Dict[str, str]]
    lead_responses: List[str]
    qualified: bool = False
    transfer_requested: bool = False
    objections_count: int = 0
    sentiment_score: float = 0.0


class AIConversationEngine:
    def __init__(self):
        # Initialize clients only if API keys are valid (not placeholder values)
        self.anthropic_client = None
        self.deepgram_client = None
        self.elevenlabs_client = None

        try:
            if (settings.ANTHROPIC_API_KEY and 
                not settings.ANTHROPIC_API_KEY.startswith('placeholder-') and
                not settings.ANTHROPIC_API_KEY.startswith('your_')):
                self.anthropic_client = anthropic.AsyncAnthropic(
                    api_key=settings.ANTHROPIC_API_KEY)
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic client: {e}")

        try:
            if (settings.DEEPGRAM_API_KEY and 
                not settings.DEEPGRAM_API_KEY.startswith('placeholder-') and
                not settings.DEEPGRAM_API_KEY.startswith('your_')):
                self.deepgram_client = Deepgram(settings.DEEPGRAM_API_KEY)
        except Exception as e:
            logger.warning(f"Failed to initialize Deepgram client: {e}")

        try:
            if (settings.ELEVENLABS_API_KEY and 
                not settings.ELEVENLABS_API_KEY.startswith('placeholder-') and
                not settings.ELEVENLABS_API_KEY.startswith('your_')):
                # Use the new ElevenLabs client initialization
                self.elevenlabs_client = elevenlabs.ElevenLabs(
                    api_key=settings.ELEVENLABS_API_KEY)
        except Exception as e:
            logger.warning(f"Failed to initialize ElevenLabs client: {e}")

        self.active_conversations: Dict[int, ConversationContext] = {}

    async def start_conversation(
            self, call_log_id: int) -> ConversationContext:
        """Initialize a new AI conversation"""
        try:
            async with get_db() as db:
                # Get call log and related data
                call_log_query = select(CallLog).where(
                    CallLog.id == call_log_id)
                call_log = await db.execute(call_log_query)
                call_log = call_log.scalar_one_or_none()

                if not call_log:
                    raise ValueError(f"Call log {call_log_id} not found")

                # Get campaign and lead info
                campaign_query = select(Campaign).where(
                    Campaign.id == call_log.campaign_id)
                campaign = await db.execute(campaign_query)
                campaign = campaign.scalar_one_or_none()

                lead_query = select(Lead).where(Lead.id == call_log.lead_id)
                lead = await db.execute(lead_query)
                lead = lead.scalar_one_or_none()

                # Create conversation context
                context = ConversationContext(
                    call_log_id=call_log_id,
                    campaign_id=call_log.campaign_id,
                    lead_id=call_log.lead_id,
                    state=ConversationState.GREETING,
                    conversation_history=[],
                    lead_responses=[]
                )

                self.active_conversations[call_log_id] = context

                # Generate initial greeting
                initial_greeting = await self._generate_initial_greeting(campaign, lead)
                context.conversation_history.append({
                    "role": "assistant",
                    "content": initial_greeting,
                    "timestamp": datetime.utcnow().isoformat()
                })

                logger.info(f"Started AI conversation for call {call_log_id}")
                return context

        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            raise

    async def process_audio_chunk(
            self,
            call_log_id: int,
            audio_data: bytes) -> Optional[bytes]:
        """Process incoming audio chunk and generate response with voicemail detection"""
        try:
            if call_log_id not in self.active_conversations:
                logger.warning(
                    f"No active conversation for call {call_log_id}")
                return None

            context = self.active_conversations[call_log_id]

            # Transcribe audio using Deepgram
            transcript = await self._transcribe_audio(audio_data)

            # Perform voicemail detection analysis
            voicemail_result = await voicemail_detection_service.analyze_audio_chunk(
                call_log_id, audio_data, transcript
            )

            # Handle voicemail detection results
            if voicemail_result.state == VoicemailState.VOICEMAIL_DETECTED:
                logger.info(f"Voicemail detected for call {call_log_id} - waiting for beep")
                # Don't respond yet, wait for beep
                return None
            
            elif voicemail_result.state == VoicemailState.BEEP_DETECTED:
                logger.info(f"Voicemail beep detected for call {call_log_id} - leaving message")
                # Generate voicemail message
                ai_response = await self._generate_voicemail_message(context)
                
                # Add to conversation history
                context.conversation_history.append({
                    "role": "assistant", 
                    "content": f"[VOICEMAIL MESSAGE] {ai_response}",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Convert to speech and return
                audio_response = await self._text_to_speech(ai_response)
                await self._log_conversation_turn(call_log_id, "[BEEP DETECTED]", ai_response)
                return audio_response

            # If no meaningful speech detected and not voicemail, continue analyzing
            if not transcript or len(transcript.strip()) < 3:
                return None

            # Add to conversation history (only if human detected or analyzing)
            context.lead_responses.append(transcript)
            context.conversation_history.append({
                "role": "user",
                "content": transcript,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Generate AI response for human conversation
            ai_response = await self._generate_ai_response(context, transcript)

            if ai_response:
                # Add AI response to history
                context.conversation_history.append({
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.utcnow().isoformat()
                })

                # Convert to speech
                audio_response = await self._text_to_speech(ai_response)

                # Log the conversation
                await self._log_conversation_turn(call_log_id, transcript, ai_response)

                return audio_response

        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return None

    async def _transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio using Deepgram"""
        try:
            if not self.deepgram_client:
                logger.warning(
                    "Deepgram client not initialized - returning mock transcript")
                return "Hello, I understand you're speaking but speech recognition is not configured."

            # Configure Deepgram options
            options = {
                'model': 'nova-2',
                'language': 'en-US',
                'punctuate': True,
                'diarize': False,
                'utterances': True,
                'interim_results': False
            }

            # Create audio source
            audio_source = {
                'buffer': audio_data,
                'mimetype': 'audio/mulaw'
            }

            # Transcribe
            response = await self.deepgram_client.transcription.prerecorded(
                audio_source, options
            )

            if response and 'results' in response:
                channels = response['results']['channels']
                if channels and len(channels) > 0:
                    alternatives = channels[0]['alternatives']
                    if alternatives and len(alternatives) > 0:
                        transcript = alternatives[0]['transcript']
                        confidence = alternatives[0]['confidence']

                        # Only return if confidence is high enough
                        if confidence > 0.7:
                            return transcript.strip()

            return None

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None

    async def _generate_ai_response(
            self,
            context: ConversationContext,
            user_input: str) -> Optional[str]:
        """Generate AI response using Claude"""
        try:
            # Get campaign and lead data for context
            async with get_db() as db:
                campaign_query = select(Campaign).where(
                    Campaign.id == context.campaign_id)
                campaign = await db.execute(campaign_query)
                campaign = campaign.scalar_one_or_none()

                lead_query = select(Lead).where(Lead.id == context.lead_id)
                lead = await db.execute(lead_query)
                lead = lead.scalar_one_or_none()

            # Build conversation context
            conversation_context = self._build_conversation_context(
                context, campaign, lead)

            # Analyze sentiment and conversation state
            await self._analyze_conversation_state(context, user_input)

            # Generate response based on current state
            response = await self._generate_contextual_response(
                context, user_input, conversation_context
            )

            return response

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return None

    async def _generate_contextual_response(
            self,
            context: ConversationContext,
            user_input: str,
            conversation_context: str) -> str:
        """Generate response based on conversation state"""
        try:
            if not self.anthropic_client:
                logger.warning(
                    "Anthropic client not initialized - returning fallback response")
                return "Thank you for your call. I'm currently experiencing technical difficulties with our AI system. Please hold while I transfer you to a human agent."

            # Build prompt based on current state
            if context.state == ConversationState.GREETING:
                prompt = self._build_greeting_prompt(
                    context, user_input, conversation_context)
            elif context.state == ConversationState.QUALIFICATION:
                prompt = self._build_qualification_prompt(
                    context, user_input, conversation_context)
            elif context.state == ConversationState.PRESENTATION:
                prompt = self._build_presentation_prompt(
                    context, user_input, conversation_context)
            elif context.state == ConversationState.OBJECTION_HANDLING:
                prompt = self._build_objection_handling_prompt(
                    context, user_input, conversation_context)
            elif context.state == ConversationState.CLOSING:
                prompt = self._build_closing_prompt(
                    context, user_input, conversation_context)
            else:
                prompt = self._build_default_prompt(
                    context, user_input, conversation_context)

            # Generate response using Claude
            response = await self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            ai_response = response.content[0].text.strip()

            # Update conversation state based on response
            self._update_conversation_state(context, user_input, ai_response)

            return ai_response

        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            return "I apologize, but I'm having trouble processing that. Could you please repeat?"

    def _build_greeting_prompt(
            self,
            context: ConversationContext,
            user_input: str,
            conversation_context: str) -> str:
        """Build prompt for greeting phase"""
        return f"""
{settings.CLAUDE_SYSTEM_PROMPT}

{conversation_context}

Current conversation state: GREETING
User just said: "{user_input}"

Your task is to:
1. Acknowledge their response warmly
2. Briefly introduce yourself and the purpose of your call
3. Begin light qualification by asking about their current situation
4. Keep response under 30 words
5. Sound natural and conversational

Generate your response:"""

    def _build_qualification_prompt(
            self,
            context: ConversationContext,
            user_input: str,
            conversation_context: str) -> str:
        """Build prompt for qualification phase"""
        return f"""
{settings.CLAUDE_SYSTEM_PROMPT}

{conversation_context}

Current conversation state: QUALIFICATION
User just said: "{user_input}"

Your task is to:
1. Ask qualifying questions to understand their needs
2. Listen for buying signals or pain points
3. Determine if they're a good fit for the product/service
4. Keep response under 35 words
5. Ask open-ended questions

Generate your response:"""

    def _build_presentation_prompt(
            self,
            context: ConversationContext,
            user_input: str,
            conversation_context: str) -> str:
        """Build prompt for presentation phase"""
        return f"""
{settings.CLAUDE_SYSTEM_PROMPT}

{conversation_context}

Current conversation state: PRESENTATION
User just said: "{user_input}"

Your task is to:
1. Present relevant benefits based on their qualification
2. Use specific examples and social proof
3. Address their particular situation
4. Keep response under 40 words
5. Make it conversational, not salesy

Generate your response:"""

    def _build_objection_handling_prompt(
            self,
            context: ConversationContext,
            user_input: str,
            conversation_context: str) -> str:
        """Build prompt for objection handling phase"""
        return f"""
{settings.CLAUDE_SYSTEM_PROMPT}

{conversation_context}

Current conversation state: OBJECTION_HANDLING
User just said: "{user_input}"

Your task is to:
1. Acknowledge their concern with empathy
2. Provide a brief, relevant response to their objection
3. Ask a follow-up question to keep engagement
4. Keep response under 35 words
5. Don't be pushy - be understanding

Generate your response:"""

    def _build_closing_prompt(
            self,
            context: ConversationContext,
            user_input: str,
            conversation_context: str) -> str:
        """Build prompt for closing phase"""
        return f"""
{settings.CLAUDE_SYSTEM_PROMPT}

{conversation_context}

Current conversation state: CLOSING
User just said: "{user_input}"

Your task is to:
1. Summarize key benefits they showed interest in
2. Suggest next steps (transfer to specialist, schedule appointment, etc.)
3. Create urgency if appropriate
4. Keep response under 30 words
5. Be direct but not aggressive

Generate your response:"""

    def _build_default_prompt(
            self,
            context: ConversationContext,
            user_input: str,
            conversation_context: str) -> str:
        """Build default prompt"""
        return f"""
{settings.CLAUDE_SYSTEM_PROMPT}

{conversation_context}

User just said: "{user_input}"

Respond naturally and helpfully while trying to guide the conversation toward a positive outcome. Keep response under 30 words.

Generate your response:"""

    def _build_conversation_context(
            self,
            context: ConversationContext,
            campaign: Any,
            lead: Any) -> str:
        """Build context for Claude"""
        return f"""
Campaign: {campaign.name}
Lead: {lead.first_name} {lead.last_name}
Phone: {lead.phone_number}
Lead Score: {lead.lead_score}
Previous Conversations: {len(context.conversation_history)}
Qualified: {context.qualified}
Objections Count: {context.objections_count}
Sentiment Score: {context.sentiment_score}
"""

    async def _analyze_conversation_state(
            self, context: ConversationContext, user_input: str):
        """Analyze conversation state and sentiment"""
        try:
            # Simple sentiment analysis based on keywords
            positive_words = [
                'yes',
                'interested',
                'good',
                'great',
                'sure',
                'okay',
                'sounds',
                'tell']
            negative_words = [
                'no',
                'not',
                'busy',
                'interested',
                'time',
                'remove',
                'stop',
                'don\'t']

            user_lower = user_input.lower()

            positive_score = sum(
                1 for word in positive_words if word in user_lower)
            negative_score = sum(
                1 for word in negative_words if word in user_lower)

            # Update sentiment score
            if positive_score > negative_score:
                context.sentiment_score = min(
                    1.0, context.sentiment_score + 0.1)
            elif negative_score > positive_score:
                context.sentiment_score = max(-1.0,
                                              context.sentiment_score - 0.1)

            # Check for objections
            objection_keywords = [
                'no',
                'not interested',
                'busy',
                'not now',
                'remove',
                'stop calling']
            if any(keyword in user_lower for keyword in objection_keywords):
                context.objections_count += 1
                context.state = ConversationState.OBJECTION_HANDLING

            # Check for transfer requests
            transfer_keywords = [
                'speak to',
                'talk to',
                'transfer',
                'manager',
                'supervisor',
                'human']
            if any(keyword in user_lower for keyword in transfer_keywords):
                context.transfer_requested = True
                context.state = ConversationState.TRANSFER

            # Check for qualification
            if context.state == ConversationState.GREETING and len(
                    context.conversation_history) > 2:
                context.state = ConversationState.QUALIFICATION
            elif context.state == ConversationState.QUALIFICATION and context.sentiment_score > 0.3:
                context.qualified = True
                context.state = ConversationState.PRESENTATION
            elif context.state == ConversationState.PRESENTATION and len(context.conversation_history) > 8:
                context.state = ConversationState.CLOSING

        except Exception as e:
            logger.error(f"Error analyzing conversation state: {e}")

    def _update_conversation_state(
            self,
            context: ConversationContext,
            user_input: str,
            ai_response: str):
        """Update conversation state based on response"""
        try:
            # Check if AI is asking for transfer
            if 'transfer' in ai_response.lower() or 'specialist' in ai_response.lower():
                context.transfer_requested = True
                context.state = ConversationState.TRANSFER

            # Check if conversation should end
            if 'goodbye' in ai_response.lower() or 'thank you' in ai_response.lower():
                context.state = ConversationState.COMPLETED

        except Exception as e:
            logger.error(f"Error updating conversation state: {e}")

    async def _text_to_speech(self, text: str) -> bytes:
        """Convert text to speech using ElevenLabs"""
        try:
            # Check if ElevenLabs is properly configured
            if (not settings.ELEVENLABS_API_KEY or
                    settings.ELEVENLABS_API_KEY.startswith('your_')):
                logger.warning(
                    "ElevenLabs not configured - returning empty audio")
                return b""

            # Use ElevenLabs functional API
            audio_bytes = self.elevenlabs_client.generate(
                text=text,
                voice=settings.ELEVENLABS_VOICE_ID,
                model="eleven_turbo_v2"
            )

            return audio_bytes

        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            # Return empty audio on error
            return b""

    async def _generate_initial_greeting(
            self, campaign: Any, lead: Any) -> str:
        """Generate initial greeting for the call"""
        try:
            greeting_templates = [
                f"Hi {lead.first_name}, this is Sarah calling about {campaign.name}. How are you doing today?",
                f"Hello {lead.first_name}, this is Sarah. I'm calling regarding {campaign.name}. Do you have a quick moment?",
                f"Hi {lead.first_name}, Sarah here about {campaign.name}. Hope you're having a good day!"]

            # Simple selection based on lead score
            if lead.lead_score > 80:
                return greeting_templates[0]
            elif lead.lead_score > 60:
                return greeting_templates[1]
            else:
                return greeting_templates[2]

        except Exception as e:
            logger.error(f"Error generating initial greeting: {e}")
            return "Hi, this is Sarah. How are you doing today?"

    async def _log_conversation_turn(
            self,
            call_log_id: int,
            user_input: str,
            ai_response: str):
        """Log conversation turn to database"""
        try:
            # For now, just log to the logger
            # TODO: Implement ConversationLog model if detailed logging is
            # needed
            logger.info(
                f"Call {call_log_id} - User: {user_input[:50]}... AI: {ai_response[:50]}...")

        except Exception as e:
            logger.error(f"Error logging conversation turn: {e}")

    async def end_conversation(self, call_log_id: int) -> Dict[str, Any]:
        """End AI conversation and clean up"""
        try:
            if call_log_id in self.active_conversations:
                context = self.active_conversations[call_log_id]

                # Generate conversation summary
                summary = {
                    'call_log_id': call_log_id,
                    'total_turns': len(context.conversation_history),
                    'qualified': context.qualified,
                    'transfer_requested': context.transfer_requested,
                    'objections_count': context.objections_count,
                    'final_sentiment_score': context.sentiment_score,
                    'final_state': context.state.value
                }

                # Update call log with conversation summary
                async with get_db() as db:
                    update_query = update(CallLog).where(
                        CallLog.id == call_log_id).values(
                        qualified=context.qualified,
                        transfer_requested=context.transfer_requested,
                        objections_count=context.objections_count,
                        sentiment_score=context.sentiment_score,
                        conversation_summary=json.dumps(summary))
                    await db.execute(update_query)
                    await db.commit()

                # Clean up
                del self.active_conversations[call_log_id]

                logger.info(f"Ended AI conversation for call {call_log_id}")
                return summary

        except Exception as e:
            logger.error(f"Error ending conversation: {e}")
            return {}

    def get_conversation_context(
            self, call_log_id: int) -> Optional[ConversationContext]:
        """Get current conversation context"""
        return self.active_conversations.get(call_log_id)

    async def should_transfer_call(self, call_log_id: int) -> bool:
        """Check if call should be transferred to human"""
        if call_log_id not in self.active_conversations:
            return False

        context = self.active_conversations[call_log_id]

        # Transfer conditions
        return (
            context.transfer_requested or
            (context.qualified and context.sentiment_score > 0.5) or
            (context.objections_count > 2 and context.sentiment_score > 0.0)
        )

    async def resume_conversation(
            self, call_log_id: int) -> ConversationContext:
        """Resume AI conversation after failed transfer"""
        try:
            # Check if conversation context exists
            if call_log_id in self.active_conversations:
                context = self.active_conversations[call_log_id]

                # Update state to indicate transfer failed
                context.state = ConversationState.OBJECTION_HANDLING
                context.transfer_requested = False

                # Add system message about transfer failure
                context.conversation_history.append({
                    "role": "system",
                    "content": "Transfer to human agent failed. Resume AI conversation.",
                    "timestamp": datetime.utcnow().isoformat()
                })

                logger.info(f"Resumed AI conversation for call {call_log_id}")
                return context
            else:
                # Restart conversation from scratch
                logger.info(
                    f"Restarting AI conversation for call {call_log_id}")
                return await self.start_conversation(call_log_id)

        except Exception as e:
            logger.error(f"Error resuming conversation: {e}")
            raise

    async def handle_transfer_success(self, call_log_id: int):
        """Handle successful transfer to human agent"""
        try:
            if call_log_id in self.active_conversations:
                context = self.active_conversations[call_log_id]

                # Update final state
                context.state = ConversationState.TRANSFER
                context.transfer_requested = True

                # Add final transfer message
                context.conversation_history.append({
                    "role": "system",
                    "content": "Successfully transferred to human agent. AI conversation ended.",
                    "timestamp": datetime.utcnow().isoformat()
                })

                # End conversation
                await self.end_conversation(call_log_id)

                logger.info(
                    f"Successfully handled transfer for call {call_log_id}")

        except Exception as e:
            logger.error(f"Error handling transfer success: {e}")

    async def _generate_voicemail_message(self, context: ConversationContext) -> str:
        """Generate appropriate voicemail message based on campaign and lead info"""
        try:
            # Get campaign and lead data for voicemail customization
            async with get_db() as db:
                campaign_query = select(Campaign).where(
                    Campaign.id == context.campaign_id)
                campaign = await db.execute(campaign_query)
                campaign = campaign.scalar_one_or_none()

                lead_query = select(Lead).where(Lead.id == context.lead_id)
                lead = await db.execute(lead_query)
                lead = lead.scalar_one_or_none()

            # Get voicemail template from voicemail detection service
            campaign_info = {
                'company_name': campaign.name if campaign else 'Our Company',
                'offer_description': campaign.description if campaign else 'an important opportunity',
                'callback_number': '1-800-CALLBACK',  # Configure this based on your needs
                'lead_name': f"{lead.first_name}" if lead and lead.first_name else "there"
            }

            # Use voicemail detection service to generate message
            voicemail_message = await voicemail_detection_service.get_voicemail_message_template(
                context.call_log_id, campaign_info
            )

            # Optionally use Claude to personalize the message further
            if self.anthropic_client and campaign and lead:
                personalization_prompt = f"""
                Personalize this voicemail message for {lead.first_name or 'the recipient'}:
                
                Base message: {voicemail_message}
                
                Campaign: {campaign.name}
                Lead info: {lead.first_name} {lead.last_name}
                
                Make it sound natural and personalized, but keep it under 30 seconds when spoken.
                Keep the same structure but add personal touches.
                """
                
                try:
                    response = await self.anthropic_client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=200,
                        temperature=0.7,
                        messages=[{"role": "user", "content": personalization_prompt}]
                    )
                    personalized_message = response.content[0].text.strip()
                    return personalized_message
                except Exception as e:
                    logger.warning(f"Failed to personalize voicemail message: {e}")

            return voicemail_message

        except Exception as e:
            logger.error(f"Error generating voicemail message: {e}")
            # Fallback message
            return """Hi, this is an automated message. We tried to reach you about an important opportunity. 
            Please call us back when you have a moment. Thank you and have a great day!"""


# Global instance
ai_conversation_engine = AIConversationEngine()


class AIConversationService:
    """Simplified AI conversation service for testing and basic usage."""
    
    def __init__(self):
        self.anthropic_client = None
        
        try:
            if (settings.ANTHROPIC_API_KEY and 
                not settings.ANTHROPIC_API_KEY.startswith('placeholder-') and
                not settings.ANTHROPIC_API_KEY.startswith('your_')):
                self.anthropic_client = anthropic.AsyncAnthropic(
                    api_key=settings.ANTHROPIC_API_KEY)
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic client: {e}")
    
    async def generate_response(self, conversation_context: str, user_input: str, call_metadata: dict) -> str:
        """Generate a simple AI response for testing."""
        if not self.anthropic_client:
            return "AI service not available (no valid API key configured)"
        
        try:
            response = await self.anthropic_client.messages.create(
                model=settings.claude_model,
                max_tokens=150,
                messages=[{
                    "role": "user",
                    "content": f"Context: {conversation_context}\nUser: {user_input}\nPlease respond naturally."
                }]
            )
            
            return response.content[0].text if response.content else "No response generated"
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return f"Error: {str(e)}"
