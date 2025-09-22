"""
Campaign Templates
Pre-built templates for different sales approaches and industries.
"""

from typing import Dict, List, Any
from enum import Enum
from app.services.guided_training import (
    BusinessObjective, BrandPersonality, IndustryType, SalesStyle
)


class TemplateType(Enum):
    CONSULTATIVE_SALES = "consultative_sales"
    APPOINTMENT_SETTING = "appointment_setting"
    LEAD_QUALIFICATION = "lead_qualification"
    DEMO_BOOKING = "demo_booking"
    FOLLOW_UP = "follow_up"
    NURTURE = "nurture"


class CampaignTemplateLibrary:
    """
    Library of pre-built campaign templates for different industries and approaches.
    """
    
    @staticmethod
    def get_template(template_type: TemplateType, industry: IndustryType) -> Dict[str, Any]:
        """
        Get a specific template by type and industry.
        """
        templates = CampaignTemplateLibrary.get_all_templates()
        
        key = f"{template_type.value}_{industry.value}"
        if key in templates:
            return templates[key]
        
        # Fall back to general template
        general_key = f"{template_type.value}_general"
        return templates.get(general_key, templates["consultative_sales_general"])
    
    @staticmethod
    def get_all_templates() -> Dict[str, Dict[str, Any]]:
        """
        Get all available templates.
        """
        return {
            # Consultative Sales Templates
            "consultative_sales_general": {
                "name": "Consultative Sales - General",
                "description": "Professional consultative approach for general sales",
                "style": SalesStyle.CONSULTATIVE,
                "brand_personality": BrandPersonality(
                    tone="professional",
                    pace="medium",
                    formality="conversational",
                    energy_level="medium",
                    empathy_level="high"
                ),
                "conversation_flow": {
                    "greeting": {"duration": 30, "focus": "rapport_building"},
                    "discovery": {"duration": 90, "focus": "needs_assessment"},
                    "presentation": {"duration": 60, "focus": "solution_matching"},
                    "objection_handling": {"duration": 45, "focus": "empathy_first"},
                    "closing": {"duration": 30, "focus": "next_steps"}
                },
                "script_template": """
                Hi [Name], this is [Agent] from [Company]. 
                
                I'm reaching out because we've been helping [similar businesses/people] with [pain point].
                
                I'd love to learn more about your current situation. 
                
                Can you tell me about [relevant question]?
                
                [Listen and respond based on their needs]
                
                Based on what you've shared, I think we might be able to help.
                
                Would you be open to a brief conversation about how we've helped others in similar situations?
                """,
                "objection_responses": {
                    "not_interested": "I understand, and I appreciate your honesty. Many of our best clients said the same thing initially. Can I ask what specifically concerns you?",
                    "too_busy": "I completely understand - everyone's busy these days. This is actually designed to save you time. Could we find just 5 minutes to see if it's a fit?",
                    "too_expensive": "I hear you on the cost concern. Let me ask - what would make this investment worthwhile for you?",
                    "need_to_think": "Absolutely, this is an important decision. What specific information would help you feel more confident?"
                }
            },
            
            "consultative_sales_solar": {
                "name": "Consultative Sales - Solar",
                "description": "Consultative approach for solar energy sales",
                "style": SalesStyle.CONSULTATIVE,
                "brand_personality": BrandPersonality(
                    tone="friendly",
                    pace="medium",
                    formality="conversational",
                    energy_level="medium",
                    empathy_level="high"
                ),
                "conversation_flow": {
                    "greeting": {"duration": 30, "focus": "homeowner_rapport"},
                    "discovery": {"duration": 90, "focus": "energy_usage_assessment"},
                    "presentation": {"duration": 60, "focus": "savings_demonstration"},
                    "objection_handling": {"duration": 45, "focus": "financial_concerns"},
                    "closing": {"duration": 30, "focus": "consultation_booking"}
                },
                "script_template": """
                Hi [Name], this is [Agent] from [Company]. 
                
                I'm calling homeowners in [Area] about the new solar incentives that just became available.
                
                Have you noticed your electric bill going up lately?
                
                We've been helping homeowners like you save $100-300 per month on their electric bills.
                
                Can you tell me roughly what you're paying for electricity each month?
                
                [Based on their bill amount]
                
                Great! Based on what you're spending, you could potentially save [amount] per month.
                
                Would you like me to have one of our energy consultants give you a free assessment?
                """,
                "objection_responses": {
                    "not_interested": "I understand. Many homeowners don't realize how much they could save. Can I ask what your main concern is about solar?",
                    "too_expensive": "I hear that a lot. The good news is there are programs where you can go solar with little to no money down. Would you like to hear about those options?",
                    "rent_dont_own": "I understand. Do you know if your landlord might be interested in reducing the property's energy costs?",
                    "roof_too_old": "That's a great question. Our consultants can assess your roof condition as part of the free evaluation. Would that be helpful?"
                }
            },
            
            "consultative_sales_insurance": {
                "name": "Consultative Sales - Insurance",
                "description": "Consultative approach for insurance sales",
                "style": SalesStyle.CONSULTATIVE,
                "brand_personality": BrandPersonality(
                    tone="professional",
                    pace="slow",
                    formality="formal",
                    energy_level="medium",
                    empathy_level="high"
                ),
                "conversation_flow": {
                    "greeting": {"duration": 30, "focus": "trust_building"},
                    "discovery": {"duration": 120, "focus": "coverage_assessment"},
                    "presentation": {"duration": 90, "focus": "protection_demonstration"},
                    "objection_handling": {"duration": 60, "focus": "risk_education"},
                    "closing": {"duration": 30, "focus": "policy_review"}
                },
                "script_template": """
                Hi [Name], this is [Agent] from [Company]. 
                
                I'm calling because you requested information about [insurance type] coverage.
                
                I'd like to make sure you have the right protection for your family's needs.
                
                Can you tell me about your current [insurance type] coverage?
                
                [Listen to their current situation]
                
                I see. Let me ask you this - what's most important to you when it comes to protecting [family/assets]?
                
                Based on what you've shared, I'd like to show you some options that might better fit your needs.
                
                Would you prefer to discuss this over the phone or would you like me to email you some information to review?
                """,
                "objection_responses": {
                    "already_covered": "That's great that you have coverage. Can I ask how recently you've reviewed your policy to make sure it still meets your needs?",
                    "too_expensive": "I understand cost is a concern. Let me ask - what would happen to your family if something unexpected occurred and you weren't adequately covered?",
                    "need_to_talk_spouse": "That makes perfect sense. Would it be helpful if I could speak with both of you together?",
                    "dont_trust_insurance": "I understand that feeling. Many people have had bad experiences. Can I ask what happened that made you feel that way?"
                }
            },
            
            # Appointment Setting Templates
            "appointment_setting_general": {
                "name": "Appointment Setting - General",
                "description": "Direct approach for setting appointments",
                "style": SalesStyle.DIRECT,
                "brand_personality": BrandPersonality(
                    tone="professional",
                    pace="fast",
                    formality="conversational",
                    energy_level="high",
                    empathy_level="medium"
                ),
                "conversation_flow": {
                    "greeting": {"duration": 20, "focus": "quick_introduction"},
                    "discovery": {"duration": 45, "focus": "pain_point_identification"},
                    "presentation": {"duration": 30, "focus": "solution_teaser"},
                    "objection_handling": {"duration": 30, "focus": "scheduling_barriers"},
                    "closing": {"duration": 20, "focus": "calendar_booking"}
                },
                "script_template": """
                Hi [Name], this is [Agent] from [Company].
                
                I'm calling because we help [target audience] with [specific problem].
                
                Are you currently dealing with [pain point]?
                
                [If yes] Great, I'd love to show you how we've helped others solve this exact problem.
                
                [If no] No worries. Let me ask you this - what's your biggest challenge with [relevant area]?
                
                Based on what you've shared, I think our [solution] could really help you.
                
                I have some time available [day] at [time] or [alternative time]. Which works better for you?
                """,
                "objection_responses": {
                    "too_busy": "I completely understand. That's exactly why I think this conversation would be valuable - to save you time. How about just 15 minutes?",
                    "not_interested": "I understand. Can I ask what you're currently doing to solve [pain point]?",
                    "send_info": "I could do that, but most people find a quick conversation more helpful. How about 10 minutes tomorrow?",
                    "call_back_later": "Sure, when would be a better time to reach you?"
                }
            },
            
            "appointment_setting_real_estate": {
                "name": "Appointment Setting - Real Estate",
                "description": "Appointment setting for real estate services",
                "style": SalesStyle.RELATIONSHIP,
                "brand_personality": BrandPersonality(
                    tone="friendly",
                    pace="medium",
                    formality="casual",
                    energy_level="high",
                    empathy_level="high"
                ),
                "conversation_flow": {
                    "greeting": {"duration": 30, "focus": "local_connection"},
                    "discovery": {"duration": 60, "focus": "property_needs"},
                    "presentation": {"duration": 45, "focus": "market_knowledge"},
                    "objection_handling": {"duration": 30, "focus": "timing_concerns"},
                    "closing": {"duration": 20, "focus": "property_viewing"}
                },
                "script_template": """
                Hi [Name], this is [Agent] from [Company] here in [Area].
                
                I'm calling homeowners in your neighborhood about the current real estate market.
                
                Have you given any thought to selling your home in the next year or two?
                
                [If yes] That's great! The market is really strong right now for sellers.
                
                [If no] I understand. Let me ask - if you could get significantly more for your home than you expected, would that change your mind?
                
                I'd love to show you what homes in your area are selling for right now.
                
                Would you be available for a quick market analysis this week? I have Tuesday at 2pm or Thursday at 6pm open.
                """,
                "objection_responses": {
                    "not_selling": "I understand. Are you happy with your current home, or is there something that might make you consider moving?",
                    "bad_market": "Actually, that's a common misconception. Let me show you what's really happening in your specific area. Would that be helpful?",
                    "have_an_agent": "That's great! A second opinion never hurts. I'd be happy to show you what I think your home is worth with no obligation.",
                    "not_ready": "I completely understand. When do you think you might be ready to consider your options?"
                }
            },
            
            # Lead Qualification Templates
            "lead_qualification_saas": {
                "name": "Lead Qualification - SaaS",
                "description": "Qualification approach for SaaS leads",
                "style": SalesStyle.SOLUTION,
                "brand_personality": BrandPersonality(
                    tone="professional",
                    pace="medium",
                    formality="conversational",
                    energy_level="medium",
                    empathy_level="medium"
                ),
                "conversation_flow": {
                    "greeting": {"duration": 25, "focus": "business_introduction"},
                    "discovery": {"duration": 90, "focus": "business_needs_assessment"},
                    "presentation": {"duration": 60, "focus": "solution_fit_demonstration"},
                    "objection_handling": {"duration": 45, "focus": "technical_concerns"},
                    "closing": {"duration": 25, "focus": "demo_scheduling"}
                },
                "script_template": """
                Hi [Name], this is [Agent] from [Company].
                
                I'm calling because you downloaded our [resource] about [topic].
                
                Are you currently using any [software category] for your business?
                
                [Listen to their current setup]
                
                I see. What's working well with your current solution, and what challenges are you facing?
                
                Based on what you've shared, it sounds like [specific pain point] is a real issue for you.
                
                I'd love to show you how we've helped other [similar businesses] solve this exact problem.
                
                Would you be interested in a brief demo to see how this might work for your business?
                """,
                "objection_responses": {
                    "happy_current_solution": "That's great! What would have to change for you to consider switching to something better?",
                    "too_complex": "I understand that concern. Our solution is actually designed to be simpler than what you're probably used to. Would you like to see how?",
                    "budget_constraints": "I hear you on budget. Can I ask what you're spending on your current solution?",
                    "not_decision_maker": "I understand. Who else would be involved in this decision? Would it be helpful to include them in our conversation?"
                }
            },
            
            # Demo Booking Templates
            "demo_booking_general": {
                "name": "Demo Booking - General",
                "description": "Direct approach for booking product demos",
                "style": SalesStyle.DIRECT,
                "brand_personality": BrandPersonality(
                    tone="professional",
                    pace="medium",
                    formality="conversational",
                    energy_level="medium",
                    empathy_level="medium"
                ),
                "conversation_flow": {
                    "greeting": {"duration": 20, "focus": "quick_value_statement"},
                    "discovery": {"duration": 45, "focus": "use_case_identification"},
                    "presentation": {"duration": 30, "focus": "demo_preview"},
                    "objection_handling": {"duration": 30, "focus": "demo_concerns"},
                    "closing": {"duration": 20, "focus": "demo_scheduling"}
                },
                "script_template": """
                Hi [Name], this is [Agent] from [Company].
                
                I'm calling because our [product] helps [target audience] [achieve specific outcome].
                
                Are you currently struggling with [specific problem]?
                
                [If yes] I'd love to show you exactly how we solve that.
                
                [If no] What's your biggest challenge with [relevant area]?
                
                Perfect! I think a quick demo would show you exactly how we can help.
                
                The demo only takes 15 minutes, and I can show you [specific benefit].
                
                I have availability tomorrow at [time] or [alternative time]. Which works better for you?
                """,
                "objection_responses": {
                    "no_time": "I understand time is tight. That's why I keep these demos to just 15 minutes. How about [specific time]?",
                    "not_interested": "I understand. Can I ask what you're currently doing to address [problem]?",
                    "send_video": "I could send you a video, but the demo is really more valuable because I can show you exactly how it would work for your specific situation.",
                    "need_approval": "No problem. Should we include your [decision maker] in the demo so they can see it too?"
                }
            },
            
            # Nurture Templates
            "nurture_general": {
                "name": "Nurture - General",
                "description": "Educational approach for nurturing leads",
                "style": SalesStyle.EDUCATIONAL,
                "brand_personality": BrandPersonality(
                    tone="friendly",
                    pace="slow",
                    formality="conversational",
                    energy_level="low",
                    empathy_level="high"
                ),
                "conversation_flow": {
                    "greeting": {"duration": 30, "focus": "relationship_building"},
                    "discovery": {"duration": 60, "focus": "situation_updates"},
                    "presentation": {"duration": 45, "focus": "educational_content"},
                    "objection_handling": {"duration": 30, "focus": "timing_concerns"},
                    "closing": {"duration": 25, "focus": "value_delivery"}
                },
                "script_template": """
                Hi [Name], this is [Agent] from [Company].
                
                I'm following up on our previous conversation about [previous topic].
                
                How have things been going with [their situation]?
                
                [Listen to updates]
                
                I wanted to share some new information that might be helpful for you.
                
                We just released [new resource/update] that addresses [their specific challenge].
                
                Would you like me to send that over to you, or would you prefer to discuss it briefly now?
                """,
                "objection_responses": {
                    "still_not_ready": "I completely understand. When do you think might be a better time to revisit this?",
                    "situation_changed": "Thanks for letting me know. How has the situation changed?",
                    "not_priority": "I understand priorities change. What's most important for you right now?",
                    "lost_interest": "I understand. Is there anything specific that changed your mind?"
                }
            }
        }
    
    @staticmethod
    def get_templates_by_industry(industry: IndustryType) -> List[Dict[str, Any]]:
        """
        Get all templates for a specific industry.
        """
        templates = CampaignTemplateLibrary.get_all_templates()
        industry_templates = []
        
        for key, template in templates.items():
            if industry.value in key or "general" in key:
                template["template_id"] = key
                industry_templates.append(template)
        
        return industry_templates
    
    @staticmethod
    def get_templates_by_style(style: SalesStyle) -> List[Dict[str, Any]]:
        """
        Get all templates for a specific sales style.
        """
        templates = CampaignTemplateLibrary.get_all_templates()
        style_templates = []
        
        for key, template in templates.items():
            if template["style"] == style:
                template["template_id"] = key
                style_templates.append(template)
        
        return style_templates
    
    @staticmethod
    def customize_template(
        template: Dict[str, Any],
        business_objective: BusinessObjective,
        industry_context: str = None
    ) -> Dict[str, Any]:
        """
        Customize a template based on specific business objectives.
        """
        customized = template.copy()
        
        # Customize script template with business-specific information
        script = customized["script_template"]
        
        # Replace placeholders with business-specific information
        if "[target audience]" in script:
            script = script.replace("[target audience]", business_objective.target_audience)
        
        if "[specific problem]" in script:
            # Extract problem from target audience or use generic
            if "with" in business_objective.target_audience:
                problem = business_objective.target_audience.split("with")[-1].strip()
                script = script.replace("[specific problem]", problem)
        
        if "[pain point]" in script:
            # Extract pain point from target audience
            pain_point = business_objective.target_audience.split()[-3:]
            script = script.replace("[pain point]", " ".join(pain_point))
        
        customized["script_template"] = script
        
        # Customize conversation flow based on primary goal
        if "appointment" in business_objective.primary_goal.lower():
            customized["conversation_flow"]["closing"]["focus"] = "appointment_booking"
        elif "demo" in business_objective.primary_goal.lower():
            customized["conversation_flow"]["closing"]["focus"] = "demo_scheduling"
        elif "lead" in business_objective.primary_goal.lower():
            customized["conversation_flow"]["closing"]["focus"] = "lead_capture"
        
        # Add industry context if provided
        if industry_context:
            customized["industry_context"] = industry_context
        
        return customized 