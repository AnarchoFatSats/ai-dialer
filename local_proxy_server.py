#!/usr/bin/env python3

import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# In-memory session storage
sessions = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0-production",
        "environment": "development"
    })

@app.route('/analytics/dashboard', methods=['GET'])
def analytics_dashboard():
    """Analytics dashboard endpoint"""
    return jsonify({
        "active_calls": 12,
        "today_transfers": 45,
        "today_revenue": 8750,
        "cost_per_transfer": 0.125,
        "transfer_rate": 18.5,
        "ai_efficiency": 94.2,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/analytics/learning-stats', methods=['GET'])
def analytics_learning_stats():
    """Analytics learning stats endpoint"""
    return jsonify({
        "progress": 78,
        "successRate": 22.5,
        "totalCalls": 1247,
        "conversions": 281,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/conversational-training/start', methods=['POST'])
def start_conversational_training():
    """Start a new conversational training session"""
    session_id = str(uuid.uuid4())
    
    # Store session
    sessions[session_id] = {
        "state": "initial",
        "history": [],
        "created_at": datetime.utcnow().isoformat()
    }
    
    return jsonify({
        "session_id": session_id,
        "message": "Hi! My name is Reach. I'm here to walk you through building the perfect campaign so the AI can create amazing prompts for a great agent ready to go. Let's start by understanding what you want to achieve with your calling campaign. What type of business are you calling for?",
        "state": "initial",
        "suggested_responses": [
            "Lead Generation",
            "Sales Outreach",
            "Customer Support",
            "Market Research", 
            "Appointment Setting",
            "Follow-up Calls"
        ]
    })

@app.route('/conversational-training/continue', methods=['POST'])
def continue_conversational_training():
    """Continue a conversational training session"""
    data = request.get_json()
    session_id = data.get('session_id')
    message = data.get('message', '')
    
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404
    
    session = sessions[session_id]
    
    # Add user message to history
    session['history'].append({
        "role": "user",
        "content": message,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Generate response based on message content
    response_message = ""
    suggested_responses = []
    new_state = "understanding_goal"
    
    if "lead generation" in message.lower():
        response_message = "Excellent! Lead generation is a powerful strategy. Now, let me understand your target audience better. Who are you trying to reach? For example, are you targeting homeowners, business owners, or a specific demographic?"
        suggested_responses = ["Homeowners", "Business owners", "Healthcare professionals", "Small business owners"]
        new_state = "clarifying_audience"
    elif "sales outreach" in message.lower():
        response_message = "Great choice! Sales outreach can be highly effective. What product or service are you selling? This will help me tailor the perfect conversation flow for your prospects."
        suggested_responses = ["Software/SaaS", "Insurance", "Solar panels", "Financial services"]
        new_state = "understanding_product"
    elif "homeowners" in message.lower():
        response_message = "Perfect! Homeowners are an excellent target. What's the main problem or need you're solving for them? This will help me create compelling conversation starters."
        suggested_responses = ["Energy savings", "Home security", "Home improvement", "Property value"]
        new_state = "identifying_pain_points"
    elif "business owners" in message.lower():
        response_message = "Excellent! Business owners are decision-makers. What's your value proposition? What specific business challenge are you helping them solve?"
        suggested_responses = ["Cost reduction", "Revenue growth", "Operational efficiency", "Compliance"]
        new_state = "defining_value_prop"
    elif "energy savings" in message.lower():
        response_message = "Energy savings is a compelling value proposition! Now, what's the typical outcome or benefit you provide? For example, do you help homeowners save money, increase home value, or become more environmentally friendly?"
        suggested_responses = ["Save money on bills", "Increase home value", "Environmental benefits", "Energy independence"]
        new_state = "defining_outcomes"
    elif "home security" in message.lower():
        response_message = "Home security is a crucial concern for many homeowners. What specific security solutions do you offer? This will help me create the right approach for your prospects."
        suggested_responses = ["Alarm systems", "Video surveillance", "Smart home security", "Professional monitoring"]
        new_state = "defining_solutions"
    elif "cost reduction" in message.lower():
        response_message = "Cost reduction is always attractive to business owners! What's the typical savings or ROI you provide? This will help me create compelling conversation points."
        suggested_responses = ["20-30% cost savings", "ROI within 6 months", "Eliminate manual processes", "Reduce overhead"]
        new_state = "quantifying_benefits"
    elif "revenue growth" in message.lower():
        response_message = "Revenue growth is the ultimate goal! How do you typically help businesses increase their revenue? This will help me craft the perfect pitch."
        suggested_responses = ["Increase sales efficiency", "Expand market reach", "Improve customer retention", "Launch new products"]
        new_state = "defining_growth_strategy"
    elif any(word in message.lower() for word in ["save money", "savings", "bills"]):
        response_message = "Excellent! Saving money is always compelling. Based on everything we've discussed, I'm ready to create your AI campaign. It will focus on lead generation for homeowners interested in energy savings. Should I create the campaign now with optimized prompts and conversation flow?"
        suggested_responses = ["Yes, create the campaign", "Let me adjust something first", "Show me a preview"]
        new_state = "ready_to_deploy"
    else:
        response_message = "That's great information! Let me help you develop this further. What's the main benefit or outcome you want prospects to achieve? This will help me create the perfect conversation flow."
        suggested_responses = ["Schedule a consultation", "Get a free quote", "Learn more about benefits", "Start a free trial"]
        new_state = "understanding_goals"
    
    # Update session state
    session['state'] = new_state
    session['history'].append({
        "role": "assistant",
        "content": response_message,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return jsonify({
        "session_id": session_id,
        "message": response_message,
        "state": new_state,
        "suggested_responses": suggested_responses
    })

@app.route('/conversational-training/history/<session_id>', methods=['GET'])
def get_conversation_history(session_id):
    """Get conversation history for a session"""
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404
    
    session = sessions[session_id]
    return jsonify({
        "session_id": session_id,
        "history": session['history'],
        "state": session['state']
    })

if __name__ == '__main__':
    print("🚀 Starting Local Proxy Server for AI Dialer")
    print("=" * 50)
    print("✅ Health endpoint: http://localhost:8080/health")
    print("✅ Analytics dashboard: http://localhost:8080/analytics/dashboard")  
    print("✅ Learning stats: http://localhost:8080/analytics/learning-stats")
    print("✅ Conversational training: http://localhost:8080/conversational-training/start")
    print("=" * 50)
    print("🎯 Frontend should connect to: http://localhost:8080")
    print("Run: npm start in amplify_ui/ and update API_BASE_URL to http://localhost:8080")
    print("=" * 50)
    
    app.run(debug=True, port=8080, host='0.0.0.0') 