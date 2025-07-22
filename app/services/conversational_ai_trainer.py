import logging
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal, get_db
from app.models import Campaign, CallLog, CallStatus, CallDisposition, Lead, CampaignStatus
from app.services.claude_service import claude_service

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    INITIAL = "initial"
    UNDERSTANDING_GOAL = "understanding_goal"
    GATHERING_CONTEXT = "gathering_context"
    CLARIFYING_AUDIENCE = "clarifying_audience"
    OPTIMIZING_APPROACH = "optimizing_approach"
    LEARNING_FROM_DATA = "learning_from_data"
    GENERATING_CAMPAIGN = "generating_campaign"
    READY_TO_DEPLOY = "ready_to_deploy"


@dataclass
class ConversationContext:
    """Stores the conversation context and gathered information"""
    session_id: str
    campaign_id: Optional[str] = None
    state: ConversationState = ConversationState.INITIAL
    
    # User Goals & Context
    primary_goal: Optional[str] = None
    target_audience: Optional[str] = None
    industry: Optional[str] = None
    product_service: Optional[str] = None
    
    # Conversation Style Preferences
    preferred_tone: Optional[str] = None
    preferred_pace: Optional[str] = None
    energy_level: Optional[str] = None
    
    # Historical Performance Data
    successful_patterns: List[Dict[str, Any]] = None
    failed_patterns: List[Dict[str, Any]] = None
    
    # Generated Configuration
    conversation_flow: Optional[Dict[str, Any]] = None
    ai_prompts: Optional[Dict[str, str]] = None
    voice_settings: Optional[Dict[str, Any]] = None
    objection_handlers: Optional[Dict[str, str]] = None
    
    # Conversation History
    conversation_history: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.successful_patterns is None:
            self.successful_patterns = []
        if self.failed_patterns is None:
            self.failed_patterns = []
        if self.conversation_history is None:
            self.conversation_history = []


@dataclass
class LearningInsight:
    """Insights derived from call performance analysis"""
    pattern_type: str  # "successful", "failed", "objection", "timing"
    confidence_score: float
    description: str
    recommendation: str
    supporting_data: Dict[str, Any]


class ConversationalAITrainer:
    """
    Conversational AI trainer that works like Claude to replace technical interfaces.
    Users can describe their goals naturally, and the system asks clarifying questions
    to build optimized campaigns while learning from call outcomes.
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, ConversationContext] = {}
        self.learning_cache: Dict[str, List[LearningInsight]] = {}
        
    async def start_conversation(self, user_id: str) -> Dict[str, Any]:
        """Start a new conversational training session"""
        session_id = str(uuid.uuid4())
        context = ConversationContext(session_id=session_id)
        self.active_sessions[session_id] = context
        
        # Initial greeting with learning from historical data
        historical_insights = await self._get_historical_insights()
        
        greeting = """👋 Hi! I'm your AI campaign trainer. I'll help you create a highly effective voice calling campaign through a simple conversation.

I've analyzed your previous campaigns and can help you build something that's optimized for success. 

**What would you like to achieve with your calling campaign?**

For example:
- "I want to book more solar consultations with homeowners"
- "I need to generate qualified insurance leads"
- "I want to increase appointment bookings for my service"

Just describe your goal in plain English, and I'll ask some questions to build the perfect campaign for you."""

        if historical_insights:
            top_insight = historical_insights[0]
            greeting += f"\n\n💡 **Quick insight**: Based on your data, {top_insight.description}"
        
        context.conversation_history.append({
            "role": "assistant",
            "content": greeting,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "session_id": session_id,
            "message": greeting,
            "state": context.state.value,
            "suggested_responses": [
                "I want to book solar consultations",
                "I need to generate insurance leads", 
                "I want to increase appointment bookings"
            ]
        }
    
    async def continue_conversation(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """Continue the conversation with user input"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found. Please start a new conversation."}
        
        context = self.active_sessions[session_id]
        
        # Add user message to history
        context.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Process based on current state
        response = await self._process_conversation_state(context, user_message)
        
        # Add assistant response to history
        context.conversation_history.append({
            "role": "assistant",
            "content": response["message"],
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return response
    
    async def _process_conversation_state(self, context: ConversationContext, user_message: str) -> Dict[str, Any]:
        """Process user input based on current conversation state"""
        
        if context.state == ConversationState.INITIAL:
            return await self._handle_initial_goal(context, user_message)
        elif context.state == ConversationState.UNDERSTANDING_GOAL:
            return await self._handle_goal_clarification(context, user_message)
        elif context.state == ConversationState.GATHERING_CONTEXT:
            return await self._handle_context_gathering(context, user_message)
        elif context.state == ConversationState.CLARIFYING_AUDIENCE:
            return await self._handle_audience_clarification(context, user_message)
        elif context.state == ConversationState.OPTIMIZING_APPROACH:
            return await self._handle_approach_optimization(context, user_message)
        elif context.state == ConversationState.LEARNING_FROM_DATA:
            return await self._handle_learning_integration(context, user_message)
        elif context.state == ConversationState.GENERATING_CAMPAIGN:
            return await self._handle_campaign_generation(context, user_message)
        else:
            return {"message": "I'm not sure how to help with that. Let's start over.", "state": context.state.value}
    
    async def _handle_initial_goal(self, context: ConversationContext, user_message: str) -> Dict[str, Any]:
        """Handle initial goal setting"""
        
        # Use Claude to understand the user's goal
        goal_analysis = await claude_service.analyze_text(
            f"Analyze this user's business goal for a calling campaign: '{user_message}'\n\n"
            f"Extract: 1) Primary objective, 2) Industry/business type, 3) Target audience hints, 4) Success metrics\n"
            f"Respond in JSON format with keys: primary_goal, industry, target_audience, success_metrics"
        )
        
        try:
            analysis = json.loads(goal_analysis)
            context.primary_goal = analysis.get("primary_goal", user_message)
            context.industry = analysis.get("industry")
            context.target_audience = analysis.get("target_audience")
        except:
            context.primary_goal = user_message
        
        # Get historical data for similar campaigns
        similar_campaigns = await self._find_similar_campaigns(context.primary_goal, context.industry)
        
        # Build conversation context for Claude
        conversation_history = self._format_conversation_history(context.conversation_history)
        
        # Create system prompt for conversational response
        system_prompt = f"""You are an expert AI campaign trainer helping a user create effective calling campaigns. 
        You have a conversational, helpful personality and guide users through campaign creation naturally.
        
        Current context:
        - User's goal: {context.primary_goal}
        - Industry: {context.industry or 'Unknown'}
        - Similar campaign success rate: {similar_campaigns[0].get('success_rate', 0):.1f}% if similar_campaigns else 'No historical data'
        
        Your task: Acknowledge their goal warmly and ask about their target audience. Be conversational and encouraging.
        Keep response under 100 words."""
        
        # Generate conversational response using Claude
        conversational_response = await claude_service.generate_content(
            prompt=f"User just said: '{user_message}'\n\nConversation so far:\n{conversation_history}\n\nPlease respond naturally and ask about their target audience.",
            system_prompt=system_prompt
        )
        
        context.state = ConversationState.UNDERSTANDING_GOAL
        
        return {
            "message": conversational_response,
            "state": context.state.value,
            "suggested_responses": [
                "Homeowners aged 30-60 with solar potential",
                "Small business owners looking for cost savings", 
                "Property managers managing multiple locations"
            ]
        }

    async def _handle_goal_clarification(self, context: ConversationContext, user_message: str) -> Dict[str, Any]:
        """Handle goal clarification phase"""
        
        # Build conversation context
        conversation_history = self._format_conversation_history(context.conversation_history)
        
        # Create system prompt for this phase
        system_prompt = f"""You are an expert AI campaign trainer. The user has shared their goal: {context.primary_goal}
        
        Now they've provided more details. Your task:
        1. Acknowledge what they shared
        2. Ask clarifying questions about their target audience or approach
        3. Be conversational and helpful
        4. Keep response under 80 words
        
        Guide them toward understanding their ideal customer profile."""
        
        # Generate conversational response
        response = await claude_service.generate_content(
            prompt=f"User just said: '{user_message}'\n\nConversation history:\n{conversation_history}\n\nPlease respond naturally and continue gathering information about their target audience.",
            system_prompt=system_prompt
        )
        
        context.state = ConversationState.GATHERING_CONTEXT
        
        return {
            "message": response,
            "state": context.state.value,
            "suggested_responses": [
                "Tell me more about their pain points",
                "What motivates them to buy?",
                "When are they most likely to answer calls?"
            ]
        }

    async def _handle_context_gathering(self, context: ConversationContext, user_message: str) -> Dict[str, Any]:
        """Handle context gathering phase"""
        
        # Store audience information
        context.target_audience = user_message
        
        # Build conversation context
        conversation_history = self._format_conversation_history(context.conversation_history)
        
        # Create system prompt
        system_prompt = f"""You are an expert AI campaign trainer. 
        
        Context:
        - Goal: {context.primary_goal}
        - Target audience info: {context.target_audience}
        
        Your task: Acknowledge their audience details and ask about their preferred conversation style/approach.
        Be conversational and keep under 80 words."""
        
        # Generate response
        response = await claude_service.generate_content(
            prompt=f"User just shared: '{user_message}'\n\nConversation:\n{conversation_history}\n\nAsk about their preferred conversation style or approach.",
            system_prompt=system_prompt
        )
        
        context.state = ConversationState.CLARIFYING_AUDIENCE
        
        return {
            "message": response,
            "state": context.state.value,
            "suggested_responses": [
                "Professional and direct approach",
                "Friendly and consultative style",
                "Educational approach with facts"
            ]
        }

    async def _handle_audience_clarification(self, context: ConversationContext, user_message: str) -> Dict[str, Any]:
        """Handle audience clarification phase"""
        
        # Store conversation preferences
        context.preferred_tone = user_message
        
        # Build conversation context
        conversation_history = self._format_conversation_history(context.conversation_history)
        
        # Create system prompt
        system_prompt = f"""You are an expert AI campaign trainer.
        
        Context:
        - Goal: {context.primary_goal}
        - Audience: {context.target_audience}
        - Preferred style: {context.preferred_tone}
        
        Your task: Acknowledge their preferences and start generating their campaign. Be excited and confident.
        Keep under 60 words."""
        
        # Generate response
        response = await claude_service.generate_content(
            prompt=f"User said: '{user_message}'\n\nConversation:\n{conversation_history}\n\nTell them you're now generating their optimized campaign.",
            system_prompt=system_prompt
        )
        
        context.state = ConversationState.GENERATING_CAMPAIGN
        
        # Generate the actual campaign
        campaign_config = await self._generate_campaign_configuration(context)
        context.conversation_flow = campaign_config
        
        return {
            "message": response + "\n\n✨ **Campaign Generated!** I've created a customized campaign based on your requirements. Would you like to review it or deploy it now?",
            "state": ConversationState.READY_TO_DEPLOY,
            "campaign_config": campaign_config,
            "suggested_responses": [
                "Show me the campaign details",
                "Deploy it now",
                "Let me make some adjustments first"
            ]
        }
    
    async def _handle_approach_optimization(self, context: ConversationContext, user_message: str) -> Dict[str, Any]:
        """Handle final optimization and campaign generation"""
        
        # Build conversation context
        conversation_history = self._format_conversation_history(context.conversation_history)
        
        if "yes" in user_message.lower() or "create" in user_message.lower() or "generate" in user_message.lower():
            context.state = ConversationState.GENERATING_CAMPAIGN
            
            # Generate the complete campaign
            campaign_config = await self._generate_campaign_configuration(context)
            
            # Use Claude to generate a conversational campaign reveal
            system_prompt = f"""You are an expert AI campaign trainer who just created a campaign.
            
            Campaign details:
            - Goal: {context.primary_goal}
            - Audience: {context.target_audience}
            - Style: {context.preferred_tone}
            
            Your task: Excitedly reveal the campaign is ready with key highlights. Be conversational and enthusiastic.
            Keep under 120 words."""
            
            response = await claude_service.generate_content(
                prompt=f"User said: '{user_message}'\n\nConversation:\n{conversation_history}\n\nReveal their completed campaign with enthusiasm!",
                system_prompt=system_prompt
            )
            
            # Store the campaign configuration
            campaign_id = await self._deploy_campaign(campaign_config, context)
            context.campaign_id = campaign_id
            context.state = ConversationState.READY_TO_DEPLOY
            
            return {
                "message": response + f"\n\n✨ **Campaign '{campaign_config.get('name', 'Custom Campaign')}' is ready to launch!**",
                "state": context.state.value,
                "campaign_id": campaign_id,
                "campaign_config": campaign_config,
                "suggested_responses": [
                    "Launch the campaign!",
                    "Show me the conversation prompts",
                    "Let me test it first"
                ]
            }
        else:
            # Use Claude to handle requests for more details
            system_prompt = f"""You are an expert AI campaign trainer. The user wants more information before creating their campaign.
            
            Context:
            - Goal: {context.primary_goal}
            - Audience: {context.target_audience}
            - Style: {context.preferred_tone}
            
            Your task: Provide helpful details about what the campaign will include. Be informative and encouraging.
            Keep under 100 words."""
            
            response = await claude_service.generate_content(
                prompt=f"User said: '{user_message}'\n\nConversation:\n{conversation_history}\n\nProvide more details about the campaign you'll create.",
                system_prompt=system_prompt
            )
            
            return {
                "message": response,
                "state": context.state.value,
                "suggested_responses": [
                    "That sounds perfect, create it!",
                    "What about objection handling?",
                    "How will it optimize performance?"
                ]
            }
    
    async def _handle_campaign_generation(self, context: ConversationContext, user_message: str) -> Dict[str, Any]:
        """Handle post-generation actions"""
        
        # Build conversation context
        conversation_history = self._format_conversation_history(context.conversation_history)
        
        if "launch" in user_message.lower() or "deploy" in user_message.lower():
            # Activate the campaign
            if context.campaign_id:
                await self._activate_campaign(context.campaign_id)
            
            # Use Claude to generate a conversational launch confirmation
            system_prompt = f"""You are an expert AI campaign trainer who just launched a user's campaign.
            
            Campaign context:
            - Goal: {context.primary_goal}
            - Audience: {context.target_audience}
            - Style: {context.preferred_tone}
            
            Your task: Excitedly confirm the campaign is live and explain what happens next. Be encouraging and specific.
            Keep under 100 words."""
            
            response = await claude_service.generate_content(
                prompt=f"User said: '{user_message}'\n\nConversation:\n{conversation_history}\n\nConfirm their campaign is now live and explain next steps!",
                system_prompt=system_prompt
            )
            
            return {
                "message": response + "\n\n🚀 **Campaign is live!** You can monitor performance in your dashboard.",
                "state": "launched",
                "campaign_id": context.campaign_id,
                "suggested_responses": [
                    "Show me the dashboard",
                    "How do I monitor performance?",
                    "Create another campaign"
                ]
            }
        
        elif "test" in user_message.lower():
            # Use Claude to explain test mode
            system_prompt = f"""You are an expert AI campaign trainer offering to test a user's campaign before full launch.
            
            Campaign context:
            - Goal: {context.primary_goal}
            - Audience: {context.target_audience}
            
            Your task: Explain how a test campaign works and its benefits. Be encouraging and explain what they'll learn.
            Keep under 80 words."""
            
            response = await claude_service.generate_content(
                prompt=f"User said: '{user_message}'\n\nConversation:\n{conversation_history}\n\nExplain how to test their campaign first.",
                system_prompt=system_prompt
            )
            
            return {
                "message": response + "\n\n🧪 **Test mode available** - Would you like to start with a small test?",
                "state": "testing",
                "suggested_responses": [
                    "Start the test",
                    "Skip test and launch",
                    "Modify the configuration"
                ]
            }
        
        else:
            # Handle requests for campaign details or other questions
            system_prompt = f"""You are an expert AI campaign trainer. The user wants to know more about their campaign before launching.
            
            Campaign context:
            - Goal: {context.primary_goal}
            - Audience: {context.target_audience}
            - Style: {context.preferred_tone}
            
            Your task: Provide helpful information about the campaign. Be informative and encourage next steps.
            Keep under 80 words."""
            
            response = await claude_service.generate_content(
                prompt=f"User said: '{user_message}'\n\nConversation:\n{conversation_history}\n\nProvide details about their campaign.",
                system_prompt=system_prompt
            )
            
            return {
                "message": response,
                "state": context.state.value,
                "suggested_responses": [
                    "Launch the campaign!",
                    "Let me test it first",
                    "Show me the conversation scripts"
                ]
            }
    
    async def _generate_optimized_campaign(self, context: ConversationContext) -> Dict[str, Any]:
        """Generate complete campaign configuration optimized from learning data"""
        
        # Get historical performance patterns
        performance_data = await self._get_performance_patterns(context)
        
        # Generate AI prompts using Claude with performance insights
        prompt_system = f"""You are an expert AI conversation designer. Create optimized conversation prompts for a calling campaign.

Goal: {context.primary_goal}
Target Audience: {context.target_audience}
Communication Style: {context.preferred_tone}

Performance Insights:
{json.dumps(performance_data, indent=2)}

Create conversation prompts for: greeting, qualification, presentation, objection_handling, closing, transfer

Make them conversational, natural, and optimized for high success rates based on the performance data."""
        
        ai_prompts_response = await claude_service.generate_content(prompt_system)
        
        # Generate objection handlers
        objection_system = f"""Create specific objection handling responses for the campaign.

Common objections based on data:
{json.dumps(await self._get_common_objections(), indent=2)}

Create empathetic, effective responses that maintain rapport while addressing concerns."""
        
        objection_handlers_response = await claude_service.generate_content(objection_system)
        
        # Generate voice settings optimized for the style
        voice_settings = await self._optimize_voice_settings(context)
        
        # Generate transfer triggers based on success patterns
        transfer_triggers = await self._generate_transfer_triggers(context)
        
        # Calculate performance projections
        projections = await self._calculate_projections(context)
        
        campaign_config = {
            "name": f"AI-Optimized {context.primary_goal} Campaign",
            "description": f"Conversational AI campaign targeting {context.target_audience}",
            "ai_prompts": self._parse_ai_prompts(ai_prompts_response),
            "objection_handlers": self._parse_objection_handlers(objection_handlers_response),
            "voice_settings": voice_settings,
            "transfer_triggers": transfer_triggers,
            "conversation_flow": await self._generate_conversation_flow(context),
            "projections": projections,
            "optimization_rules": await self._generate_optimization_rules(context)
        }
        
        return campaign_config
    
    async def _get_historical_insights(self) -> List[LearningInsight]:
        """Get insights from historical campaign performance"""
        
        async with AsyncSessionLocal() as session:
            try:
                # Get top performing patterns
                top_campaigns = await session.execute(
                    select(Campaign, 
                           func.count(CallLog.id).label('total_calls'),
                           func.sum(func.case((CallLog.disposition == CallDisposition.TRANSFER, 1), else_=0)).label('transfers'))
                    .join(CallLog, Campaign.id == CallLog.campaign_id)
                    .group_by(Campaign.id)
                    .having(func.count(CallLog.id) > 50)
                    .order_by(desc('transfers'))
                    .limit(3)
                )
                
                insights = []
                for campaign, total_calls, transfers in top_campaigns:
                    success_rate = (transfers / total_calls * 100) if total_calls > 0 else 0
                    
                    insight = LearningInsight(
                        pattern_type="successful",
                        confidence_score=min(total_calls / 100, 1.0),
                        description=f"campaigns with {campaign.ai_tone} tone achieved {success_rate:.1f}% success rate",
                        recommendation=f"Consider using {campaign.ai_tone} approach for better results",
                        supporting_data={"campaign_id": str(campaign.id), "success_rate": success_rate}
                    )
                    insights.append(insight)
                
                return insights
                
            except Exception as e:
                logger.error(f"Error getting historical insights: {e}")
                return []
    
    async def _find_similar_campaigns(self, goal: str, industry: str) -> List[Dict[str, Any]]:
        """Find similar campaigns based on goal and industry"""
        
        async with AsyncSessionLocal() as session:
            try:
                # Simple text matching for now - could be enhanced with semantic search
                query = select(Campaign).where(
                    or_(
                        Campaign.name.ilike(f"%{industry}%") if industry else False,
                        Campaign.description.ilike(f"%{goal}%") if goal else False
                    )
                ).limit(5)
                
                result = await session.execute(query)
                campaigns = result.scalars().all()
                
                similar_campaigns = []
                for campaign in campaigns:
                    # Calculate success rate
                    stats = await self._get_campaign_stats(campaign.id, session)
                    similar_campaigns.append({
                        "id": str(campaign.id),
                        "name": campaign.name,
                        "success_rate": stats.get("success_rate", 0)
                    })
                
                return sorted(similar_campaigns, key=lambda x: x["success_rate"], reverse=True)
                
            except Exception as e:
                logger.error(f"Error finding similar campaigns: {e}")
                return []
    
    async def _get_campaign_stats(self, campaign_id: str, session: AsyncSession) -> Dict[str, Any]:
        """Get campaign performance statistics"""
        
        try:
            stats_query = select(
                func.count(CallLog.id).label('total_calls'),
                func.sum(func.case((CallLog.status == CallStatus.ANSWERED, 1), else_=0)).label('answered'),
                func.sum(func.case((CallLog.disposition == CallDisposition.TRANSFER, 1), else_=0)).label('transfers')
            ).where(CallLog.campaign_id == campaign_id)
            
            result = await session.execute(stats_query)
            stats = result.first()
            
            total_calls = stats.total_calls or 0
            answered = stats.answered or 0
            transfers = stats.transfers or 0
            
            return {
                "total_calls": total_calls,
                "answer_rate": (answered / total_calls * 100) if total_calls > 0 else 0,
                "success_rate": (transfers / answered * 100) if answered > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign stats: {e}")
            return {}
    
    async def _analyze_performance_patterns(self, context: ConversationContext) -> List[LearningInsight]:
        """Analyze performance patterns to generate insights"""
        
        async with AsyncSessionLocal() as session:
            try:
                # Analyze successful call patterns
                successful_calls = await session.execute(
                    select(CallLog)
                    .where(CallLog.disposition == CallDisposition.TRANSFER)
                    .where(CallLog.initiated_at >= datetime.utcnow() - timedelta(days=30))
                    .limit(100)
                )
                
                # Analyze failed call patterns
                failed_calls = await session.execute(
                    select(CallLog)
                    .where(CallLog.disposition.in_([CallDisposition.HANGUP, CallDisposition.NOT_INTERESTED]))
                    .where(CallLog.initiated_at >= datetime.utcnow() - timedelta(days=30))
                    .limit(100)
                )
                
                insights = []
                
                # Analyze timing patterns
                timing_insight = await self._analyze_timing_patterns(session)
                if timing_insight:
                    insights.append(timing_insight)
                
                # Analyze objection patterns
                objection_insight = await self._analyze_objection_patterns(session)
                if objection_insight:
                    insights.append(objection_insight)
                
                # Analyze conversation length patterns
                duration_insight = await self._analyze_duration_patterns(session)
                if duration_insight:
                    insights.append(duration_insight)
                
                return insights
                
            except Exception as e:
                logger.error(f"Error analyzing performance patterns: {e}")
                return []
    
    async def _deploy_campaign(self, campaign_config: Dict[str, Any], context: ConversationContext) -> str:
        """Deploy the generated campaign to the database"""
        
        async with AsyncSessionLocal() as session:
            try:
                campaign = Campaign(
                    name=campaign_config["name"],
                    description=campaign_config["description"],
                    status=CampaignStatus.DRAFT,
                    
                    # AI Configuration
                    greeting_prompt=campaign_config["ai_prompts"].get("greeting"),
                    qualification_prompt=campaign_config["ai_prompts"].get("qualification"),
                    presentation_prompt=campaign_config["ai_prompts"].get("presentation"),
                    objection_handling_prompt=campaign_config["ai_prompts"].get("objection_handling"),
                    closing_prompt=campaign_config["ai_prompts"].get("closing"),
                    transfer_prompt=campaign_config["ai_prompts"].get("transfer"),
                    
                    # Voice Settings
                    voice_id=campaign_config["voice_settings"].get("voice_id"),
                    voice_speed=campaign_config["voice_settings"].get("speed"),
                    voice_pitch=campaign_config["voice_settings"].get("pitch"),
                    
                    # Conversational AI Training Data
                    training_data=json.dumps({
                        "conversation_context": asdict(context),
                        "optimization_rules": campaign_config["optimization_rules"],
                        "learning_insights": [asdict(insight) for insight in await self._get_historical_insights()]
                    })
                )
                
                session.add(campaign)
                await session.commit()
                await session.refresh(campaign)
                
                return str(campaign.id)
                
            except Exception as e:
                logger.error(f"Error deploying campaign: {e}")
                raise
    
    async def _activate_campaign(self, campaign_id: str) -> None:
        """Activate the campaign for live calling"""
        
        async with AsyncSessionLocal() as session:
            try:
                await session.execute(
                    update(Campaign)
                    .where(Campaign.id == campaign_id)
                    .values(status=CampaignStatus.ACTIVE)
                )
                await session.commit()
                
            except Exception as e:
                logger.error(f"Error activating campaign: {e}")
                raise
    
    # Helper methods for parsing and analysis
    def _parse_ai_prompts(self, response: str) -> Dict[str, str]:
        """Parse AI prompts from Claude response"""
        # Simple parsing - could be enhanced with structured output
        prompts = {
            "greeting": "You are a professional AI assistant making outbound calls. Greet the person warmly and introduce yourself.",
            "qualification": "Ask qualifying questions to understand if this person is a good fit for the service.",
            "presentation": "Present the key benefits in a compelling but natural way.",
            "objection_handling": "Address objections with empathy and provide reassuring responses.",
            "closing": "Guide the conversation toward the next step - booking an appointment or transferring to a specialist.",
            "transfer": "Prepare the person for transfer to a human agent with relevant context."
        }
        
        # TODO: Implement more sophisticated parsing of Claude's response
        return prompts
    
    def _parse_objection_handlers(self, response: str) -> Dict[str, str]:
        """Parse objection handlers from Claude response"""
        # Simple default handlers - could be enhanced with Claude parsing
        return {
            "not_interested": "I understand, and I don't want to waste your time. Can I ask what specifically you're not interested in?",
            "no_time": "I completely understand - everyone's busy. This will just take 2 minutes. What time would work better for you?",
            "too_expensive": "I hear that a lot, and cost is definitely important. Can I show you how this actually saves money in the long run?",
            "need_to_think": "That's totally reasonable. What specific information would help you make the decision?"
        }
    
    # Additional helper methods would be implemented here...
    async def _optimize_voice_settings(self, context: ConversationContext) -> Dict[str, Any]:
        """Optimize voice settings based on context"""
        return {
            "voice_id": "rachel",
            "speed": 1.1,
            "pitch": 1.0,
            "emphasis": "medium"
        }
    
    async def _generate_transfer_triggers(self, context: ConversationContext) -> List[str]:
        """Generate transfer triggers based on success patterns"""
        return [
            "Customer expresses strong interest",
            "Customer asks about pricing or next steps",
            "Customer wants to speak with a specialist",
            "Customer is ready to move forward"
        ]
    
    async def _calculate_projections(self, context: ConversationContext) -> Dict[str, float]:
        """Calculate performance projections"""
        return {
            "answer_rate": 65.0,
            "qualification_rate": 25.0,
            "transfer_rate": 18.0
        }
    
    async def _generate_conversation_flow(self, context: ConversationContext) -> Dict[str, Any]:
        """Generate conversation flow structure"""
        return {
            "stages": ["greeting", "qualification", "presentation", "objection_handling", "closing", "transfer"],
            "max_objections": 3,
            "qualification_required": True
        }
    
    async def _generate_optimization_rules(self, context: ConversationContext) -> List[Dict[str, Any]]:
        """Generate optimization rules for continuous learning"""
        return [
            {
                "rule": "improve_answer_rate",
                "condition": "answer_rate < 60%",
                "action": "adjust_timing_and_approach"
            },
            {
                "rule": "optimize_objection_handling",
                "condition": "objection_count > 2",
                "action": "refine_objection_responses"
            }
        ]
    
    # Additional analysis methods
    async def _analyze_timing_patterns(self, session: AsyncSession) -> Optional[LearningInsight]:
        """Analyze optimal calling times"""
        # Implementation would analyze call success by time of day
        return None
    
    async def _analyze_objection_patterns(self, session: AsyncSession) -> Optional[LearningInsight]:
        """Analyze common objections and successful responses"""
        # Implementation would analyze objection handling success
        return None
    
    async def _analyze_duration_patterns(self, session: AsyncSession) -> Optional[LearningInsight]:
        """Analyze optimal conversation duration"""
        # Implementation would analyze call duration vs success rate
        return None
    
    async def _get_audience_insights(self, audience: str) -> List[LearningInsight]:
        """Get insights about specific audience types"""
        return []
    
    async def _get_style_performance(self, style: str) -> Optional[Dict[str, Any]]:
        """Get performance data for communication styles"""
        return None
    
    async def _get_objection_insights(self, objection: str) -> List[LearningInsight]:
        """Get insights about handling specific objections"""
        return []
    
    async def _get_performance_patterns(self, context: ConversationContext) -> Dict[str, Any]:
        """Get performance patterns for optimization"""
        return {}
    
    async def _get_common_objections(self) -> List[Dict[str, Any]]:
        """Get common objections from call data"""
        return []
    
    async def _provide_more_details(self, context: ConversationContext, user_message: str) -> Dict[str, Any]:
        """Provide more details about the campaign"""
        return {"message": "Let me provide more details...", "state": context.state.value}
    
    async def _show_campaign_details(self, context: ConversationContext, user_message: str) -> Dict[str, Any]:
        """Show detailed campaign configuration"""
        return {"message": "Here are the campaign details...", "state": context.state.value}

    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for Claude context"""
        formatted = []
        for msg in history[-10:]:  # Only include last 10 messages to stay within token limits
            role = "Assistant" if msg["role"] == "assistant" else "User"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)


# Global instance
conversational_ai_trainer = ConversationalAITrainer() 