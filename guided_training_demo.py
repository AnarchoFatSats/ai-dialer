#!/usr/bin/env python3
"""
Guided Training System Demo

This script demonstrates how to use the new guided training system to create
AI campaigns from business objectives and sales scripts.

The system transforms user-friendly inputs into complete AI campaign configurations.
"""

import asyncio
import json
from typing import Dict, Any


class GuidedTrainingDemo:
    """
    Demo class showcasing the guided training system workflow.
    """
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
    
    def print_section(self, title: str):
        """Print a formatted section header."""
        print(f"\n{'='*60}")
        print(f"🎯 {title}")
        print(f"{'='*60}")
    
    def print_step(self, step: str):
        """Print a formatted step."""
        print(f"\n📝 {step}")
        print("-" * 50)

    def demo_workflow(self):
        """Demonstrate the complete guided training workflow."""
        
        self.print_section("GUIDED TRAINING SYSTEM DEMO")
        
        print("""
        This demo shows how to transform business objectives and sales scripts
        into complete AI campaign configurations using the guided training system.
        
        🚀 WHAT THIS SYSTEM DOES:
        - Analyzes your sales script to extract key components
        - Generates AI conversation flows from business objectives
        - Creates voice settings based on brand personality
        - Builds objection handlers automatically
        - Configures qualification criteria and transfer triggers
        - Deploys a complete, ready-to-use AI campaign
        """)
        
        # Sample business objectives
        business_objectives = {
            "primary_goal": "book solar consultations",
            "target_audience": "homeowners with high electric bills",
            "success_metrics": ["50 consultations per week", "20% conversion rate"],
            "budget_constraints": {"max_cost_per_lead": 30.0},
            "timeline": "3 months"
        }
        
        # Sample sales script
        sales_script = """
        Hi [Name], this is [Agent] from SolarMax Solutions.
        
        I'm calling homeowners in [Area] about the new solar incentives that just became available.
        
        Have you noticed your electric bill going up lately? Many homeowners are seeing 20-30% increases.
        
        We've been helping homeowners like you eliminate their electric bills entirely and even earn money back from the utility company.
        
        Can you tell me roughly what you're paying for electricity each month?
        
        Based on what you're spending, you could potentially save $150-250 per month with solar.
        
        The best part is, there are programs where you can go solar with zero money down.
        
        Would you like me to have one of our energy consultants give you a free assessment to see exactly how much you could save?
        """
        
        # Sample brand personality
        brand_personality = {
            "brand_tone": "friendly",
            "brand_pace": "medium",
            "brand_formality": "conversational",
            "energy_level": "medium",
            "empathy_level": "high"
        }
        
        # Demo Step 1: Script Analysis
        self.print_step("STEP 1: Analyze Sales Script")
        print(f"📄 SALES SCRIPT:\n{sales_script}")
        
        print(f"\n🎯 API CALL: POST /guided-training/analyze-script")
        print(f"Payload: {{'sales_script': '<script>', 'industry': 'solar'}}")
        
        expected_analysis = {
            "greeting": "Hi [Name], this is [Agent] from SolarMax Solutions.",
            "value_proposition": "eliminate their electric bills entirely and even earn money back",
            "qualification_questions": [
                "Have you noticed your electric bill going up lately?",
                "Can you tell me roughly what you're paying for electricity each month?"
            ],
            "key_benefits": [
                "eliminate their electric bills entirely",
                "save $150-250 per month with solar",
                "zero money down programs"
            ],
            "call_to_action": "Would you like me to have one of our energy consultants give you a free assessment"
        }
        
        print(f"\n✅ EXPECTED ANALYSIS RESULT:")
        print(json.dumps(expected_analysis, indent=2))
        
        # Demo Step 2: Preview Campaign Configuration
        self.print_step("STEP 2: Preview Campaign Configuration")
        print(f"🎯 BUSINESS OBJECTIVES:")
        print(json.dumps(business_objectives, indent=2))
        
        print(f"\n🎨 BRAND PERSONALITY:")
        print(json.dumps(brand_personality, indent=2))
        
        print(f"\n🎯 API CALL: POST /guided-training/preview-campaign")
        
        expected_preview = {
            "campaign_name": "Solar Consultation Campaign 202501",
            "conversation_flow": {
                "greeting": {"duration": 30, "focus": "homeowner_rapport"},
                "discovery": {"duration": 90, "focus": "energy_usage_assessment"},
                "presentation": {"duration": 60, "focus": "savings_demonstration"},
                "objection_handling": {"duration": 45, "focus": "financial_concerns"},
                "closing": {"duration": 30, "focus": "consultation_booking"}
            },
            "voice_settings": {
                "voice_id": "pNInz6obpgDQGcFmaJgB",
                "voice_name": "Adam",
                "voice_speed": 1.0,
                "voice_pitch": 1.0,
                "voice_emphasis": "medium"
            },
            "objection_handlers": {
                "too_expensive": "I hear that a lot. The good news is there are programs where you can go solar with little to no money down.",
                "not_interested": "I understand. Many homeowners don't realize how much they could save. Can I ask what your main concern is about solar?"
            }
        }
        
        print(f"\n✅ EXPECTED PREVIEW RESULT:")
        print(json.dumps(expected_preview, indent=2))
        
        # Demo Step 3: Create Complete Campaign
        self.print_step("STEP 3: Create Complete Campaign")
        
        full_request = {
            **business_objectives,
            **brand_personality,
            "sales_script": sales_script,
            "industry": "solar"
        }
        
        print(f"🎯 API CALL: POST /guided-training/create-campaign")
        print(f"Payload: {json.dumps(full_request, indent=2)}")
        
        expected_result = {
            "success": True,
            "campaign_id": "uuid-generated-id",
            "campaign_name": "Solar Consultation Campaign 202501",
            "message": "Campaign created successfully from guided training",
            "configuration": {
                "conversation_flow": "...",
                "voice_settings": "...",
                "objection_handlers": "...",
                "qualification_criteria": "...",
                "transfer_triggers": "...",
                "success_metrics": "..."
            }
        }
        
        print(f"\n✅ EXPECTED RESULT:")
        print(json.dumps(expected_result, indent=2))
        
        # Demo Step 4: Alternative Template-Based Approach
        self.print_step("STEP 4: Alternative - Use Pre-Built Templates")
        
        print(f"🎯 API CALL: GET /guided-training/templates?industry=solar")
        
        expected_templates = [
            {
                "template_id": "consultative_sales_solar",
                "name": "Consultative Sales - Solar",
                "description": "Consultative approach for solar energy sales",
                "style": "consultative"
            },
            {
                "template_id": "appointment_setting_general",
                "name": "Appointment Setting - General",
                "description": "Direct approach for setting appointments",
                "style": "direct"
            }
        ]
        
        print(f"\n✅ AVAILABLE TEMPLATES:")
        print(json.dumps(expected_templates, indent=2))
        
        print(f"\n🎯 API CALL: POST /guided-training/customize-template")
        template_request = {
            "template_id": "consultative_sales_solar",
            "business_objective": business_objectives,
            "customizations": {"industry_context": "residential solar"}
        }
        
        print(f"Payload: {json.dumps(template_request, indent=2)}")
        
        # Demo Step 5: Additional Helper Endpoints
        self.print_step("STEP 5: Additional Helper Endpoints")
        
        print(f"🎯 Get Voice Suggestions: POST /guided-training/suggest-voice")
        print(f"Payload: {{'brand_tone': 'friendly', 'industry': 'solar'}}")
        
        print(f"\n🎯 Generate Objection Responses: POST /guided-training/generate-objections")
        print(f"Payload: {{'sales_script': '<script>', 'brand_tone': 'friendly'}}")
        
        print(f"\n🎯 Get Supported Industries: GET /guided-training/industries")
        print(f"🎯 Get Supported Styles: GET /guided-training/styles")
        
        # Demo Summary
        self.print_section("SYSTEM BENEFITS")
        
        print("""
        ✅ BEFORE vs AFTER:
        
        BEFORE (Manual Configuration):
        - User needs to understand AI prompt engineering
        - Separate configuration of voice, prompts, objections
        - Technical complexity requires AI expertise
        - Time-consuming manual setup
        
        AFTER (Guided Training):
        - User provides business goals and sales script
        - System automatically generates complete configuration
        - No technical AI knowledge required
        - Campaign ready in minutes, not hours
        
        🚀 KEY FEATURES:
        - Script Analysis: Automatically extracts key components
        - AI Prompt Generation: Creates stage-specific prompts
        - Voice Personality Matching: Selects optimal voice settings
        - Objection Handler Generation: Creates contextual responses
        - Qualification Criteria: Extracts from business objectives
        - Transfer Triggers: Defines when to escalate to humans
        - Template Library: Pre-built industry-specific templates
        - Preview Mode: See configuration before deployment
        
        🎯 WORKFLOW OPTIONS:
        1. Complete Guided Creation: Business objectives + script → Full campaign
        2. Template-Based: Start with template → Customize → Deploy
        3. Component-by-Component: Analyze script → Generate parts → Assemble
        """)
        
        print(f"\n{'='*60}")
        print("🎉 GUIDED TRAINING SYSTEM DEMO COMPLETE!")
        print(f"{'='*60}")

    def api_examples(self):
        """Show practical API usage examples."""
        
        self.print_section("API USAGE EXAMPLES")
        
        examples = [
            {
                "title": "Solar Company - Appointment Setting",
                "description": "A solar company wants to book consultations with homeowners",
                "request": {
                    "primary_goal": "book solar consultations",
                    "target_audience": "homeowners with high electric bills",
                    "success_metrics": ["50 consultations per week"],
                    "sales_script": "Hi, I'm calling about solar savings in your area...",
                    "brand_tone": "friendly",
                    "industry": "solar"
                }
            },
            {
                "title": "Insurance Agency - Lead Generation",
                "description": "An insurance agency wants to generate qualified leads",
                "request": {
                    "primary_goal": "generate qualified insurance leads",
                    "target_audience": "families with inadequate life insurance",
                    "success_metrics": ["30 qualified leads per week"],
                    "sales_script": "Hi, I'm calling about life insurance protection...",
                    "brand_tone": "professional",
                    "industry": "insurance"
                }
            },
            {
                "title": "SaaS Company - Demo Booking",
                "description": "A SaaS company wants to book product demos",
                "request": {
                    "primary_goal": "book product demos",
                    "target_audience": "small business owners using spreadsheets",
                    "success_metrics": ["25 demos per week", "15% conversion rate"],
                    "sales_script": "Hi, I'm calling about automating your business processes...",
                    "brand_tone": "professional",
                    "industry": "saas"
                }
            }
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"\n{i}. {example['title']}")
            print(f"   {example['description']}")
            print(f"   Request: {json.dumps(example['request'], indent=6)}")


if __name__ == "__main__":
    demo = GuidedTrainingDemo()
    
    # Run the complete demo
    demo.demo_workflow()
    
    # Show practical examples
    demo.api_examples()
    
    print(f"\n🔗 To test these endpoints:")
    print(f"1. Start your backend server: python3 -m uvicorn app.main:app --reload")
    print(f"2. Visit: http://localhost:8000/docs")
    print(f"3. Look for the 'Guided Training' section")
    print(f"4. Try the endpoints with the sample data above") 