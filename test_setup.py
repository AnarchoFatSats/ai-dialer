#!/usr/bin/env python3
"""
Test script to verify the AI Dialer setup works correctly.
"""
import os
import sys
import asyncio
from app.config import Settings
from app.services.ai_conversation import AIConversationService

async def test_setup():
    """Test the basic setup and configuration."""
    print("🔧 Testing AI Dialer Setup...")
    
    # Test configuration loading
    try:
        settings = Settings()
        print("✅ Configuration loaded successfully")
        print(f"   - Environment: {settings.environment}")
        print(f"   - Claude Model: {settings.claude_model}")
        print(f"   - AWS Connect Instance ID: {settings.aws_connect_instance_id}")
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False
    
    # Test Claude API if key is available
    if settings.anthropic_api_key:
        try:
            ai_service = AIConversationService()
            response = await ai_service.generate_response(
                conversation_context="Test conversation",
                user_input="Hello, this is a test message.",
                call_metadata={}
            )
            print("✅ Claude API test successful")
            print(f"   - Response: {response[:100]}...")
        except Exception as e:
            print(f"❌ Claude API test failed: {e}")
            return False
    else:
        print("⚠️  Claude API key not configured - skipping API test")
    
    print("🎉 Setup test completed successfully!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_setup())
    sys.exit(0 if success else 1) 