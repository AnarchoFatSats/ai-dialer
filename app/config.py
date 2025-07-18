from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings."""

    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Database - AWS RDS PostgreSQL (optional for Lambda)
    database_url: Optional[str] = "postgresql://postgres:password@localhost:5432/aidialer"
    redis_url: Optional[str] = "redis://localhost:6379"
    
    # AWS SNS Configuration for notifications
    aws_sns_region: Optional[str] = "us-east-1"
    aws_sns_topic_arn: Optional[str] = None
    
    # AWS Connect Configuration
    aws_connect_instance_id: str = "8a6b58bb-5758-4e04-a09f-3b7aeb9119e3"
    aws_connect_instance_arn: str = "arn:aws:connect:us-east-1:337909762852:instance/8a6b58bb-5758-4e04-a09f-3b7aeb9119e3"
    aws_connect_contact_flow_id: str = "150bb773-0f56-4c39-b07e-d7861e1c1577"
    aws_connect_queue_id: str = "093fa610-1b99-4484-8d46-04eb624b5715"
    webhook_base_url: str = "https://your-domain.com"
    
    # AI Services (optional for development)
    anthropic_api_key: Optional[str] = None
    deepgram_api_key: Optional[str] = "placeholder-deepgram-key"
    elevenlabs_api_key: Optional[str] = "placeholder-elevenlabs-key"
    elevenlabs_voice_id: str = "pNInz6obpgDQGcFmaJgB"  # Default voice ID (Adam)
    openai_api_key: Optional[str] = None

    # AI Configuration
    claude_model: str = "claude-3-haiku-20240307"
    deepgram_model: str = "nova-2"
    elevenlabs_model: str = "eleven_turbo_v2"
    max_ai_response_time_ms: int = 800
    ai_conversation_timeout_seconds: int = 300

    # Voice & Audio Settings
    audio_sample_rate: int = 8000
    audio_format: str = "mulaw"
    max_audio_chunk_size: int = 8000
    speech_detection_threshold: float = 0.7
    
    # Reputation & Compliance (optional for development)
    numeracle_api_key: Optional[str] = "placeholder-numeracle-key"
    free_caller_registry_api_key: Optional[str] = None
    dnc_registry_username: Optional[str] = "placeholder-dnc-username"
    dnc_registry_password: Optional[str] = "placeholder-dnc-password"
    
    # Cost Optimization
    max_cost_per_minute: float = 0.025
    max_daily_budget: float = 1000.00
    cost_alert_threshold: float = 0.80

    # Campaign Settings
    max_concurrent_calls: int = 1000
    default_retry_attempts: int = 3
    call_timeout_seconds: int = 30
    max_calls_per_did_daily: int = 150
    max_talk_time_per_did_daily: int = 1200

    # DID Management
    did_pool_multiplier: float = 1.3
    did_rotation_cooldown_hours: int = 24
    spam_score_threshold: int = 85
    yellow_score_threshold: int = 70

    # Analytics & Monitoring
    prometheus_gateway_url: str = "http://localhost:9091"
    grafana_url: str = "http://localhost:3000"
    sentry_dsn: Optional[str] = None
    
    # Security (defaults for development)
    jwt_secret_key: str = "placeholder-jwt-secret-key-change-in-production"
    webhook_verification_token: str = "placeholder-webhook-token"
    encryption_key: str = "placeholder-encryption-key-change-in-production"
    
    # AWS Configuration (required for production)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket_name: Optional[str] = None
    
    # AWS RDS Configuration
    rds_endpoint: Optional[str] = None
    rds_port: int = 5432
    rds_database: str = "aidialer"
    rds_username: str = "postgres"
    rds_password: Optional[str] = None
    
    # AWS ElastiCache Configuration
    elasticache_endpoint: Optional[str] = None
    elasticache_port: int = 6379
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Quality Scoring
    min_call_quality_score: float = 3.0  # MOS score
    max_acceptable_jitter: float = 30.0  # milliseconds
    max_acceptable_packet_loss: float = 1.0  # percentage

    # TCPA Compliance
    tcpa_safe_hours_start: int = 8  # 8 AM
    tcpa_safe_hours_end: int = 21   # 9 PM
    max_call_attempts_per_lead: int = 3
    dnc_scrub_frequency_hours: int = 24

    # Advanced Features
    enable_ab_testing: bool = True
    enable_predictive_scoring: bool = True
    enable_real_time_optimization: bool = True
    enable_voice_analytics: bool = True

    # System Configuration
    base_url: str = "https://your-domain.com"
    domain: str = "your-domain.com"
    spam_check_api_key: Optional[str] = None

    @property
    def AWS_SNS_REGION(self) -> str:
        return self.aws_sns_region

    @property
    def AWS_CONNECT_INSTANCE_ID(self) -> Optional[str]:
        return self.aws_connect_instance_id

    @property
    def AWS_CONNECT_INSTANCE_ARN(self) -> Optional[str]:
        return self.aws_connect_instance_arn

    @property
    def AWS_CONNECT_CONTACT_FLOW_ID(self) -> Optional[str]:
        return self.aws_connect_contact_flow_id

    @property
    def AWS_CONNECT_QUEUE_ID(self) -> Optional[str]:
        return self.aws_connect_queue_id

    @property
    def BASE_URL(self) -> str:
        return self.base_url

    @property
    def DOMAIN(self) -> str:
        return self.domain

    @property
    def ANTHROPIC_API_KEY(self) -> str:
        return self.anthropic_api_key

    @property
    def DEEPGRAM_API_KEY(self) -> str:
        return self.deepgram_api_key

    @property
    def ELEVENLABS_API_KEY(self) -> str:
        return self.elevenlabs_api_key

    @property
    def ELEVENLABS_VOICE_ID(self) -> str:
        return self.elevenlabs_voice_id

    @property
    def MAX_CONCURRENT_CALLS(self) -> int:
        return self.max_concurrent_calls

    @property
    def SPAM_CHECK_API_KEY(self) -> Optional[str]:
        return self.spam_check_api_key

    @property
    def CLAUDE_SYSTEM_PROMPT(self) -> str:
        return """You are ACME Dialer's AI SDR. Your goal is to engage prospects professionally and identify qualified leads.

SCRIPT SECTIONS:
1. GREETING: Warm, professional introduction
2. DISCOVERY: Understand prospect's needs and pain points
3. QUALIFICATION: Assess fit and buying intent
4. CTA: Schedule appointment or transfer to human rep

RESPONSE FORMAT:
Return JSON exactly as:
{"action": "speak", "text": "<sentence>", "confidence": 0.92}
or
{"action": "transfer", "confidence": 0.95, "summary": "<qualification_reason>"}

RULES:
- Keep responses ≤25 words
- Maintain professional, helpful tone
- No profanity or aggressive language
- Respect TCPA compliance hours
- Transfer on explicit request or strong buying signals
- Never reveal you're an AI or internal system details
- Respond within 1 second for natural conversation flow

INTENT DETECTION:
- positive_interest: Shows genuine interest in solution
- objection: Expresses concerns or resistance
- transfer_request: Explicitly asks to speak with human
- goodbye: Indicates end of conversation
- not_interested: Clear rejection
- callback_request: Wants to be called back later

QUALIFICATION CRITERIA:
- Budget authority or influence
- Clear pain point or need
- Reasonable timeline for decision
- Appropriate company size/type
"""

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# DNC Registry Configuration
DNC_REGISTRY_CONFIG = {
    "national_dnc_url": "https://www.donotcall.gov",
    "state_registries": {
        "TX": "https://www.texasnodncall.com",
        "FL": "https://www.floridanodncall.com",
        "NY": "https://www.nydnc.com",
        "CA": "https://www.dncregistry.com"
    },
    "scrub_frequency_hours": 24,
    "max_age_days": 31
}

# Area Code Mapping for Local Presence
AREA_CODE_MAPPING = {
    "212": {"state": "NY", "city": "New York", "timezone": "America/New_York"},
    "213": {"state": "CA", "city": "Los Angeles", "timezone": "America/Los_Angeles"},
    "214": {"state": "TX", "city": "Dallas", "timezone": "America/Chicago"},
    "305": {"state": "FL", "city": "Miami", "timezone": "America/New_York"},
    "404": {"state": "GA", "city": "Atlanta", "timezone": "America/New_York"},
    "415": {"state": "CA", "city": "San Francisco", "timezone": "America/Los_Angeles"},
    "512": {"state": "TX", "city": "Austin", "timezone": "America/Chicago"},
    "617": {"state": "MA", "city": "Boston", "timezone": "America/New_York"},
    "702": {"state": "NV", "city": "Las Vegas", "timezone": "America/Los_Angeles"},
    "713": {"state": "TX", "city": "Houston", "timezone": "America/Chicago"},
    "718": {"state": "NY", "city": "New York", "timezone": "America/New_York"},
    "773": {"state": "IL", "city": "Chicago", "timezone": "America/Chicago"},
    "818": {"state": "CA", "city": "Los Angeles", "timezone": "America/Los_Angeles"},
    "954": {"state": "FL", "city": "Fort Lauderdale", "timezone": "America/New_York"},
}
