"""
Guided Training Service
Transforms business objectives and sales scripts into AI campaign configurations.
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import anthropic
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Campaign, CampaignStatus

logger = logging.getLogger(__name__)


class SalesStyle(Enum):
    CONSULTATIVE = "consultative"
    DIRECT = "direct"
    EDUCATIONAL = "educational"
    RELATIONSHIP = "relationship"
    SOLUTION = "solution"


class IndustryType(Enum):
    SOLAR = "solar"
    INSURANCE = "insurance"
    REAL_ESTATE = "real_estate"
    SAAS = "saas"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    GENERAL = "general"


@dataclass
class BusinessObjective:
    """User's business objectives for the campaign"""
    primary_goal: str  # "book appointments", "generate leads", "close sales"
    target_audience: str  # "homeowners with high electric bills"
    success_metrics: List[str]  # ["50 appointments/week", "$20K+ prospects"]
    budget_constraints: Dict[str, float]  # {"max_cost_per_lead": 25.0}
    timeline: str  # "6 months", "ongoing"


@dataclass
class SalesScript:
    """Analyzed sales script with extracted components"""
    raw_script: str
    greeting: str
    value_proposition: str
    qualification_questions: List[str]
    objection_responses: Dict[str, str]
    closing_statements: List[str]
    key_benefits: List[str]
    pain_points: List[str]
    call_to_action: str


@dataclass
class BrandPersonality:
    """Brand voice and personality configuration"""
    tone: str  # "professional", "friendly", "authoritative"
    pace: str  # "fast", "medium", "slow"
    formality: str  # "formal", "casual", "conversational"
    energy_level: str  # "high", "medium", "low"
    empathy_level: str  # "high", "medium", "low"


@dataclass
class GeneratedCampaign:
    """Complete campaign configuration generated from user inputs"""
    name: str
    description: str
    conversation_flow: Dict[str, Any]
    ai_prompts: Dict[str, str]
    voice_settings: Dict[str, Any]
    objection_handlers: Dict[str, str]
    qualification_criteria: Dict[str, Any]
    transfer_triggers: List[str]
    success_metrics: Dict[str, Any]


class GuidedTrainingService:
    """
    Main service for guided campaign creation.
    Converts business objectives and sales scripts into AI configurations.
    """
    
    def __init__(self):
        self.anthropic_client = None
        
        # Initialize Claude client for script analysis
        try:
            if (settings.ANTHROPIC_API_KEY and 
                not settings.ANTHROPIC_API_KEY.startswith('placeholder-')):
                self.anthropic_client = anthropic.AsyncAnthropic(
                    api_key=settings.ANTHROPIC_API_KEY)
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic client: {e}")
    
    async def create_guided_campaign(
        self,
        objectives: BusinessObjective,
        sales_script: str,
        brand_personality: BrandPersonality,
        industry: IndustryType = IndustryType.GENERAL
    ) -> GeneratedCampaign:
        """
        Main method to create a complete campaign from user inputs.
        """
        try:
            logger.info(f"Starting guided campaign creation for: {objectives.primary_goal}")
            
            # Step 1: Analyze the sales script
            analyzed_script = await self._analyze_sales_script(sales_script, industry)
            
            # Step 2: Generate conversation flow
            conversation_flow = await self._generate_conversation_flow(
                objectives, analyzed_script, brand_personality
            )
            
            # Step 3: Create AI prompts for each conversation stage
            ai_prompts = await self._generate_ai_prompts(
                objectives, analyzed_script, brand_personality, conversation_flow
            )
            
            # Step 4: Configure voice settings
            voice_settings = await self._configure_voice_settings(
                brand_personality, industry
            )
            
            # Step 5: Generate objection handlers
            objection_handlers = await self._generate_objection_handlers(
                analyzed_script, brand_personality
            )
            
            # Step 6: Set qualification criteria
            qualification_criteria = await self._extract_qualification_criteria(
                objectives, analyzed_script
            )
            
            # Step 7: Define transfer triggers
            transfer_triggers = await self._define_transfer_triggers(
                objectives, analyzed_script
            )
            
            # Step 8: Configure success metrics
            success_metrics = await self._configure_success_metrics(objectives)
            
            # Generate campaign name if not provided
            campaign_name = await self._generate_campaign_name(objectives, industry)
            
            return GeneratedCampaign(
                name=campaign_name,
                description=f"AI-generated campaign for {objectives.primary_goal}",
                conversation_flow=conversation_flow,
                ai_prompts=ai_prompts,
                voice_settings=voice_settings,
                objection_handlers=objection_handlers,
                qualification_criteria=qualification_criteria,
                transfer_triggers=transfer_triggers,
                success_metrics=success_metrics
            )
            
        except Exception as e:
            logger.error(f"Error creating guided campaign: {e}")
            raise
    
    async def _analyze_sales_script(
        self, 
        script: str, 
        industry: IndustryType
    ) -> SalesScript:
        """
        Analyze the sales script to extract key components.
        """
        if not self.anthropic_client:
            # Fallback to basic regex analysis
            return await self._basic_script_analysis(script)
        
        analysis_prompt = f"""
        Analyze this sales script and extract the following components:

        SCRIPT:
        {script}

        INDUSTRY: {industry.value}

        Please extract and return JSON with:
        {{
            "greeting": "opening greeting/introduction",
            "value_proposition": "main value proposition",
            "qualification_questions": ["question1", "question2"],
            "objection_responses": {{"objection": "response"}},
            "closing_statements": ["closing1", "closing2"],
            "key_benefits": ["benefit1", "benefit2"],
            "pain_points": ["pain1", "pain2"],
            "call_to_action": "what action is requested"
        }}

        Focus on extracting actual text from the script, not creating new content.
        """
        
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            # Extract JSON from response
            response_text = response.content[0].text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                analysis = json.loads(json_match.group())
                return SalesScript(
                    raw_script=script,
                    greeting=analysis.get("greeting", ""),
                    value_proposition=analysis.get("value_proposition", ""),
                    qualification_questions=analysis.get("qualification_questions", []),
                    objection_responses=analysis.get("objection_responses", {}),
                    closing_statements=analysis.get("closing_statements", []),
                    key_benefits=analysis.get("key_benefits", []),
                    pain_points=analysis.get("pain_points", []),
                    call_to_action=analysis.get("call_to_action", "")
                )
            else:
                logger.warning("Could not extract JSON from script analysis")
                return await self._basic_script_analysis(script)
                
        except Exception as e:
            logger.error(f"Error analyzing script with Claude: {e}")
            return await self._basic_script_analysis(script)
    
    async def _basic_script_analysis(self, script: str) -> SalesScript:
        """
        Basic script analysis using regex patterns.
        """
        lines = script.split('\n')
        
        # Extract greeting (first few lines)
        greeting = ' '.join(lines[:3]).strip()
        
        # Look for questions
        questions = [line.strip() for line in lines if '?' in line]
        
        # Look for benefits (lines with "benefit", "save", "help", etc.)
        benefit_keywords = ['benefit', 'save', 'help', 'reduce', 'increase', 'improve']
        benefits = []
        for line in lines:
            if any(keyword in line.lower() for keyword in benefit_keywords):
                benefits.append(line.strip())
        
        # Extract call to action (lines with "schedule", "book", "call", etc.)
        cta_keywords = ['schedule', 'book', 'call', 'meet', 'appointment']
        cta = ""
        for line in lines:
            if any(keyword in line.lower() for keyword in cta_keywords):
                cta = line.strip()
                break
        
        return SalesScript(
            raw_script=script,
            greeting=greeting,
            value_proposition=' '.join(lines[3:6]).strip(),
            qualification_questions=questions[:5],
            objection_responses={},
            closing_statements=lines[-3:],
            key_benefits=benefits[:5],
            pain_points=[],
            call_to_action=cta
        )
    
    async def _generate_conversation_flow(
        self,
        objectives: BusinessObjective,
        script: SalesScript,
        personality: BrandPersonality
    ) -> Dict[str, Any]:
        """
        Generate conversation flow structure.
        """
        flow = {
            "greeting": {
                "purpose": "Build rapport and introduce purpose",
                "max_duration": 30,
                "key_elements": [script.greeting, "establish credibility"],
                "success_criteria": ["prospect responds positively", "shows interest"]
            },
            "discovery": {
                "purpose": "Understand prospect's situation and needs",
                "max_duration": 60,
                "key_elements": script.qualification_questions,
                "success_criteria": ["gather qualification info", "identify pain points"]
            },
            "presentation": {
                "purpose": "Present relevant solutions",
                "max_duration": 90,
                "key_elements": script.key_benefits,
                "success_criteria": ["address specific needs", "demonstrate value"]
            },
            "objection_handling": {
                "purpose": "Address concerns and resistance",
                "max_duration": 45,
                "key_elements": list(script.objection_responses.keys()),
                "success_criteria": ["overcome objections", "rebuild interest"]
            },
            "closing": {
                "purpose": "Secure commitment or next steps",
                "max_duration": 30,
                "key_elements": [script.call_to_action],
                "success_criteria": [objectives.primary_goal]
            }
        }
        
        return flow
    
    async def _generate_ai_prompts(
        self,
        objectives: BusinessObjective,
        script: SalesScript,
        personality: BrandPersonality,
        flow: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate AI prompts for each conversation stage.
        """
        base_context = f"""
        You are a {personality.tone} AI sales representative.
        
        CAMPAIGN OBJECTIVE: {objectives.primary_goal}
        TARGET AUDIENCE: {objectives.target_audience}
        
        PERSONALITY:
        - Tone: {personality.tone}
        - Pace: {personality.pace}
        - Formality: {personality.formality}
        - Energy: {personality.energy_level}
        - Empathy: {personality.empathy_level}
        
        VALUE PROPOSITION: {script.value_proposition}
        
        RULES:
        - Keep responses under 25 words
        - Sound natural and conversational
        - Focus on the prospect's needs
        - Use the provided script elements as guidance
        - Never reveal you're an AI
        """
        
        prompts = {}
        
        # Greeting prompt
        prompts["greeting"] = f"""
        {base_context}
        
        GREETING PHASE:
        Your goal: {flow['greeting']['purpose']}
        Script reference: {script.greeting}
        
        When user responds, acknowledge warmly and introduce the purpose of your call.
        Use the script as guidance but adapt to their response.
        """
        
        # Discovery prompt
        prompts["discovery"] = f"""
        {base_context}
        
        DISCOVERY PHASE:
        Your goal: {flow['discovery']['purpose']}
        Key questions to explore: {', '.join(script.qualification_questions[:3])}
        
        Ask relevant questions to understand their situation.
        Listen for pain points and opportunities.
        """
        
        # Presentation prompt
        prompts["presentation"] = f"""
        {base_context}
        
        PRESENTATION PHASE:
        Your goal: {flow['presentation']['purpose']}
        Key benefits to highlight: {', '.join(script.key_benefits[:3])}
        
        Present solutions that address their specific needs.
        Use benefits from the script that match their situation.
        """
        
        # Objection handling prompt
        prompts["objection_handling"] = f"""
        {base_context}
        
        OBJECTION HANDLING PHASE:
        Your goal: {flow['objection_handling']['purpose']}
        
        Acknowledge their concern with empathy.
        Provide a brief, relevant response.
        Ask a follow-up question to re-engage.
        """
        
        # Closing prompt
        prompts["closing"] = f"""
        {base_context}
        
        CLOSING PHASE:
        Your goal: {flow['closing']['purpose']}
        Call to action: {script.call_to_action}
        
        Summarize key benefits they showed interest in.
        Suggest next steps: {objectives.primary_goal}
        Create appropriate urgency without being pushy.
        """
        
        return prompts
    
    async def _configure_voice_settings(
        self,
        personality: BrandPersonality,
        industry: IndustryType
    ) -> Dict[str, Any]:
        """
        Configure voice settings based on personality and industry.
        """
        # Voice mapping based on personality
        voice_mapping = {
            "professional": {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel"},
            "friendly": {"voice_id": "pNInz6obpgDQGcFmaJgB", "name": "Adam"},
            "authoritative": {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella"},
            "conversational": {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi"}
        }
        
        # Speed mapping
        speed_mapping = {
            "fast": 1.2,
            "medium": 1.0,
            "slow": 0.8
        }
        
        # Industry-specific adjustments
        industry_adjustments = {
            IndustryType.FINANCE: {"formality": "formal", "speed": 0.9},
            IndustryType.HEALTHCARE: {"empathy": "high", "speed": 0.9},
            IndustryType.SOLAR: {"energy": "medium", "speed": 1.0},
            IndustryType.INSURANCE: {"trust": "high", "speed": 0.9}
        }
        
        base_voice = voice_mapping.get(personality.tone, voice_mapping["professional"])
        
        settings = {
            "voice_id": base_voice["voice_id"],
            "voice_name": base_voice["name"],
            "voice_speed": speed_mapping.get(personality.pace, 1.0),
            "voice_pitch": 1.0,
            "voice_emphasis": "medium",
            "voice_model": "eleven_turbo_v2"
        }
        
        # Apply industry adjustments
        if industry in industry_adjustments:
            adjustments = industry_adjustments[industry]
            if "speed" in adjustments:
                settings["voice_speed"] = adjustments["speed"]
        
        return settings
    
    async def _generate_objection_handlers(
        self,
        script: SalesScript,
        personality: BrandPersonality
    ) -> Dict[str, str]:
        """
        Generate objection handling responses.
        """
        base_handlers = {
            "not_interested": f"I understand, and I appreciate your honesty. Many of our best customers said the same thing initially. Can I ask what specifically concerns you?",
            "too_expensive": f"I hear you on the cost concern. Let me ask - what would make this investment worthwhile for you?",
            "need_to_think": f"Absolutely, this is an important decision. What specific information would help you feel more confident?",
            "not_now": f"I understand timing is important. When would be a better time to revisit this?",
            "speak_to_spouse": f"That makes perfect sense. Would it be helpful if I could speak with both of you together?",
            "already_have_solution": f"That's great that you're already working on this. How is your current solution working for you?",
            "too_busy": f"I completely understand - everyone's busy these days. This is actually designed to save you time. Could we find just 5 minutes to see if it's a fit?"
        }
        
        # Enhance with script-specific objections
        enhanced_handlers = base_handlers.copy()
        enhanced_handlers.update(script.objection_responses)
        
        return enhanced_handlers
    
    async def _extract_qualification_criteria(
        self,
        objectives: BusinessObjective,
        script: SalesScript
    ) -> Dict[str, Any]:
        """
        Extract qualification criteria from objectives and script.
        """
        criteria = {
            "required_fields": [],
            "scoring_factors": {},
            "disqualifiers": [],
            "ideal_profile": {}
        }
        
        # Extract from objectives
        if "budget" in objectives.target_audience.lower():
            criteria["required_fields"].append("budget_authority")
        
        if "homeowner" in objectives.target_audience.lower():
            criteria["required_fields"].append("owns_home")
        
        # Extract from script questions
        for question in script.qualification_questions:
            if "budget" in question.lower():
                criteria["scoring_factors"]["budget_mentioned"] = 10
            if "timeline" in question.lower():
                criteria["scoring_factors"]["timeline_mentioned"] = 8
            if "decision" in question.lower():
                criteria["scoring_factors"]["decision_maker"] = 12
        
        # Set disqualifiers
        criteria["disqualifiers"] = [
            "not_decision_maker",
            "no_budget",
            "competitor_customer",
            "do_not_call_request"
        ]
        
        return criteria
    
    async def _define_transfer_triggers(
        self,
        objectives: BusinessObjective,
        script: SalesScript
    ) -> List[str]:
        """
        Define when to transfer to human agent.
        """
        triggers = [
            "explicit_transfer_request",
            "ready_to_buy_signals",
            "complex_technical_questions",
            "pricing_negotiation",
            "contract_discussion"
        ]
        
        # Add objective-specific triggers
        if "appointment" in objectives.primary_goal.lower():
            triggers.append("calendar_scheduling")
        
        if "high_value" in objectives.target_audience.lower():
            triggers.append("qualified_high_value_prospect")
        
        return triggers
    
    async def _configure_success_metrics(
        self,
        objectives: BusinessObjective
    ) -> Dict[str, Any]:
        """
        Configure success metrics based on objectives.
        """
        metrics = {
            "primary_goal": objectives.primary_goal,
            "target_metrics": objectives.success_metrics,
            "kpis": {}
        }
        
        # Default KPIs
        metrics["kpis"] = {
            "contact_rate": {"target": 0.3, "weight": 0.2},
            "conversation_rate": {"target": 0.6, "weight": 0.25},
            "qualification_rate": {"target": 0.4, "weight": 0.3},
            "transfer_rate": {"target": 0.2, "weight": 0.25}
        }
        
        # Adjust based on primary goal
        if "appointment" in objectives.primary_goal.lower():
            metrics["kpis"]["appointment_rate"] = {"target": 0.15, "weight": 0.4}
        
        if "lead" in objectives.primary_goal.lower():
            metrics["kpis"]["lead_generation_rate"] = {"target": 0.25, "weight": 0.35}
        
        return metrics
    
    async def _generate_campaign_name(
        self,
        objectives: BusinessObjective,
        industry: IndustryType
    ) -> str:
        """
        Generate a descriptive campaign name.
        """
        industry_names = {
            IndustryType.SOLAR: "Solar",
            IndustryType.INSURANCE: "Insurance",
            IndustryType.REAL_ESTATE: "Real Estate",
            IndustryType.SAAS: "SaaS",
            IndustryType.HEALTHCARE: "Healthcare",
            IndustryType.FINANCE: "Financial",
            IndustryType.GENERAL: "Sales"
        }
        
        goal_actions = {
            "appointment": "Appointment Setting",
            "lead": "Lead Generation",
            "sale": "Sales",
            "demo": "Demo Booking",
            "consultation": "Consultation"
        }
        
        industry_name = industry_names.get(industry, "Sales")
        
        # Extract action from primary goal
        action = "Outreach"
        for key, value in goal_actions.items():
            if key in objectives.primary_goal.lower():
                action = value
                break
        
        timestamp = datetime.now().strftime("%Y%m")
        
        return f"{industry_name} {action} Campaign {timestamp}"
    
    async def deploy_campaign(
        self,
        generated_campaign: GeneratedCampaign,
        db: AsyncSession
    ) -> Campaign:
        """
        Deploy the generated campaign configuration to the database.
        """
        try:
            # Create campaign record
            campaign = Campaign(
                name=generated_campaign.name,
                description=generated_campaign.description,
                status=CampaignStatus.DRAFT,
                
                # AI Configuration
                system_prompt=generated_campaign.ai_prompts.get("system"),
                greeting_prompt=generated_campaign.ai_prompts.get("greeting"),
                qualification_prompt=generated_campaign.ai_prompts.get("discovery"),
                presentation_prompt=generated_campaign.ai_prompts.get("presentation"),
                objection_prompt=generated_campaign.ai_prompts.get("objection_handling"),
                closing_prompt=generated_campaign.ai_prompts.get("closing"),
                
                # Voice Configuration
                voice_id=generated_campaign.voice_settings.get("voice_id"),
                voice_speed=generated_campaign.voice_settings.get("voice_speed"),
                voice_pitch=generated_campaign.voice_settings.get("voice_pitch"),
                voice_emphasis=generated_campaign.voice_settings.get("voice_emphasis"),
                voice_model=generated_campaign.voice_settings.get("voice_model"),
                
                # Conversation Configuration
                conversation_config=generated_campaign.conversation_flow,
                objection_responses=list(generated_campaign.objection_handlers.values()),
                
                # Training Status
                training_status="completed",
                training_started_at=datetime.utcnow(),
                training_config={
                    "method": "guided_creation",
                    "qualification_criteria": generated_campaign.qualification_criteria,
                    "transfer_triggers": generated_campaign.transfer_triggers,
                    "success_metrics": generated_campaign.success_metrics
                }
            )
            
            db.add(campaign)
            await db.commit()
            await db.refresh(campaign)
            
            logger.info(f"Successfully deployed guided campaign: {campaign.name}")
            return campaign
            
        except Exception as e:
            logger.error(f"Error deploying campaign: {e}")
            await db.rollback()
            raise


# Global instance
guided_training_service = GuidedTrainingService() 