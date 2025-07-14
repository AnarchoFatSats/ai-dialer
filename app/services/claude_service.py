import logging
import asyncio
from typing import Dict, Any, List, Optional
import json
import httpx
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ClaudeResponse:
    """Response from Claude API"""
    content: str
    usage: Dict[str, Any]
    model: str
    stop_reason: str


class ClaudeService:
    """
    Service for interacting with Claude AI for natural language processing
    used by the conversational AI trainer.
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'anthropic_api_key', None)
        self.base_url = "https://api.anthropic.com/v1"
        self.model = "claude-3-haiku-20240307"  # Fast model for conversational use
        self.max_tokens = 1000
        
    async def generate_content(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate content using Claude"""
        try:
            if not self.api_key:
                logger.warning("Claude API key not configured, using fallback")
                return await self._fallback_generation(prompt)
            
            async with httpx.AsyncClient() as client:
                messages = [{"role": "user", "content": prompt}]
                
                payload = {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "messages": messages
                }
                
                if system_prompt:
                    payload["system"] = system_prompt
                
                headers = {
                    "x-api-key": self.api_key,
                    "content-type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
                
                response = await client.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["content"][0]["text"]
                else:
                    logger.error(f"Claude API error: {response.status_code} - {response.text}")
                    return await self._fallback_generation(prompt)
                    
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return await self._fallback_generation(prompt)
    
    async def analyze_text(self, text: str) -> str:
        """Analyze text and return insights"""
        system_prompt = """You are an expert at analyzing text for business insights. 
        Provide clear, actionable analysis in a structured format."""
        
        return await self.generate_content(text, system_prompt)
    
    async def create_conversation_prompts(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Create conversation prompts optimized for the given context"""
        
        prompt = f"""Create AI conversation prompts for a calling campaign with these details:

Goal: {context.get('primary_goal', 'Generate leads')}
Target Audience: {context.get('target_audience', 'General audience')}
Communication Style: {context.get('preferred_tone', 'Professional')}

Create prompts for each stage:
1. Greeting - warm, professional introduction
2. Qualification - questions to identify fit
3. Presentation - compelling benefit presentation
4. Objection Handling - empathetic responses
5. Closing - guide to next steps
6. Transfer - prepare for human handoff

Return as JSON with keys: greeting, qualification, presentation, objection_handling, closing, transfer

Each prompt should be:
- Conversational and natural
- Under 100 words
- Optimized for phone conversations
- Appropriate for the target audience"""

        response = await self.generate_content(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse Claude response as JSON")
            return await self._fallback_prompts(context)
    
    async def create_objection_handlers(self, common_objections: List[str], context: Dict[str, Any]) -> Dict[str, str]:
        """Create objection handling responses"""
        
        objections_text = "\n".join([f"- {obj}" for obj in common_objections])
        
        prompt = f"""Create effective objection handling responses for these common objections:

{objections_text}

Context:
- Goal: {context.get('primary_goal', 'Generate leads')}
- Audience: {context.get('target_audience', 'General audience')}
- Style: {context.get('preferred_tone', 'Professional')}

For each objection, create a response that:
- Acknowledges the concern with empathy
- Provides reassurance or clarification
- Keeps the conversation moving forward
- Maintains rapport and trust

Return as JSON with objection keywords as keys and responses as values."""

        response = await self.generate_content(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return await self._fallback_objection_handlers(common_objections)
    
    async def optimize_conversation_flow(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize conversation flow based on performance data"""
        
        prompt = f"""Analyze this call performance data and suggest conversation flow optimizations:

Performance Data:
{json.dumps(performance_data, indent=2)}

Identify:
1. Stages where people drop off most
2. Successful conversation patterns
3. Optimal conversation length
4. Best timing for key messages

Provide specific recommendations for improving:
- Answer rates
- Qualification rates
- Transfer rates
- Overall success

Return as JSON with optimization recommendations."""

        response = await self.generate_content(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return await self._fallback_optimization()
    
    async def _fallback_generation(self, prompt: str) -> str:
        """Fallback when Claude API is unavailable"""
        logger.info("Using fallback generation")
        
        # Simple keyword-based responses
        if "goal" in prompt.lower():
            return "I understand you want to achieve your business goals through effective calling campaigns."
        elif "audience" in prompt.lower():
            return "Understanding your target audience is crucial for campaign success."
        elif "objection" in prompt.lower():
            return "Handling objections with empathy and providing value is key to success."
        else:
            return "I'm here to help you create an effective calling campaign. Let me know what specific assistance you need."
    
    async def _fallback_prompts(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Fallback conversation prompts"""
        return {
            "greeting": f"Hello, this is [Agent Name] calling from [Company]. I hope you're having a great day. I'm reaching out because we help people with {context.get('primary_goal', 'their business needs')}. Do you have a quick moment to chat?",
            "qualification": "I'd love to learn more about your situation. Are you currently [relevant qualifier question based on service]?",
            "presentation": f"Based on what you've shared, I think we could really help you {context.get('primary_goal', 'achieve your goals')}. Here's how it works...",
            "objection_handling": "I completely understand your concern. Let me address that for you...",
            "closing": "This sounds like it could be a great fit for your needs. What would be the best next step for you?",
            "transfer": "I'd love to connect you with our specialist who can provide more detailed information and help you get started. Is now a good time for that?"
        }
    
    async def _fallback_objection_handlers(self, objections: List[str]) -> Dict[str, str]:
        """Fallback objection handlers"""
        return {
            "not_interested": "I understand, and I don't want to waste your time. Can I ask what specifically you're not interested in?",
            "no_time": "I completely understand - everyone's busy. This will just take 2 minutes. What time would work better for you?",
            "too_expensive": "I hear that a lot, and cost is definitely important. Can I show you how this actually saves money in the long run?",
            "need_to_think": "That's totally reasonable. What specific information would help you make the decision?",
            "already_have_solution": "That's great that you have something in place. How is it working for you? Are there any areas where you'd like to see improvement?"
        }
    
    async def _fallback_optimization(self) -> Dict[str, Any]:
        """Fallback optimization recommendations"""
        return {
            "recommendations": [
                "Focus on building rapport in the first 30 seconds",
                "Ask open-ended questions to understand needs",
                "Address objections with empathy before providing solutions",
                "Keep initial presentation under 2 minutes",
                "Establish clear next steps before ending calls"
            ],
            "timing_optimization": {
                "optimal_call_length": "3-5 minutes",
                "max_objections_before_transfer": 3,
                "qualification_time": "60-90 seconds"
            }
        }


# Global instance
claude_service = ClaudeService() 