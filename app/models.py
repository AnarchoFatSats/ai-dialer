from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON, Enum, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum
from datetime import datetime
from typing import Optional, Dict, Any

# Enums for status fields
class LeadStatus(enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    CALLBACK = "callback"
    DNC = "dnc"
    CONVERTED = "converted"

class CallStatus(enum.Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BUSY = "busy"
    NO_ANSWER = "no_answer"

class DIDStatus(enum.Enum):
    CLEAN = "clean"
    YELLOW = "yellow"
    RED = "red"
    QUARANTINE = "quarantine"
    COOLING_OFF = "cooling_off"

class CampaignStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class CallDisposition(enum.Enum):
    TRANSFER = "transfer"
    VOICEMAIL = "voicemail"
    HANGUP = "hangup"
    NOT_INTERESTED = "not_interested"
    CALLBACK = "callback"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"

# Campaign Models
class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    
    # Campaign Configuration
    script_template = Column(Text, nullable=False)
    max_concurrent_calls = Column(Integer, default=10)
    call_timeout_seconds = Column(Integer, default=30)
    retry_attempts = Column(Integer, default=3)
    retry_delay_minutes = Column(Integer, default=60)
    
    # Transfer Settings
    transfer_number = Column(String(20))
    backup_transfer_number = Column(String(20))
    transfer_on_qualification = Column(Boolean, default=True)
    
    # AI & Script Configuration
    ai_prompt = Column(Text)
    greeting_message = Column(Text)
    objection_responses = Column(ARRAY(Text))
    
    # AI Training Configuration
    system_prompt = Column(Text)
    greeting_prompt = Column(Text)
    qualification_prompt = Column(Text)
    presentation_prompt = Column(Text)
    objection_prompt = Column(Text)
    closing_prompt = Column(Text)
    ai_temperature = Column(Float, default=0.7)
    ai_max_tokens = Column(Integer, default=200)
    ai_response_length = Column(Integer, default=30)
    
    # Voice Configuration
    voice_id = Column(String(50), default="rachel")
    voice_speed = Column(Float, default=1.0)
    voice_pitch = Column(Float, default=1.0)
    voice_emphasis = Column(String(20), default="medium")
    voice_model = Column(String(50), default="eleven_turbo_v2")
    
    # Conversation Configuration
    conversation_style = Column(String(50), default="consultative")
    conversation_config = Column(JSON)
    objections_before_transfer = Column(Integer, default=3)
    
    # Training Status
    training_status = Column(String(20), default="not_started")
    training_started_at = Column(DateTime)
    training_config = Column(JSON)
    
    # A/B Testing Configuration
    ab_test_config = Column(JSON)
    
    # Campaign Settings
    max_daily_budget = Column(Float, default=1000.0)
    cost_per_minute_limit = Column(Float, default=0.025)
    
    # Timing & Scheduling
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    daily_start_hour = Column(Integer, default=8)
    daily_end_hour = Column(Integer, default=21)
    timezone = Column(String(50), default="America/New_York")
    
    # Campaign Metrics
    total_leads = Column(Integer, default=0)
    leads_called = Column(Integer, default=0)
    leads_contacted = Column(Integer, default=0)
    leads_qualified = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    
    # A/B Testing
    ab_test_enabled = Column(Boolean, default=False)
    ab_test_variants = Column(JSON)
    
    # Relationships
    leads = relationship("Lead", back_populates="campaign")
    call_logs = relationship("CallLog", back_populates="campaign")
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Campaign(name='{self.name}', status='{self.status}')>"

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    
    # Contact Information
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255))
    phone = Column(String(20), nullable=False)
    phone_number = Column(String(20))  # Alias for phone
    company = Column(String(255))
    title = Column(String(100))
    
    # Geographic Information
    area_code = Column(String(3))
    state = Column(String(2))
    city = Column(String(100))
    timezone = Column(String(50))
    
    # Lead Status & Scoring
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    score = Column(Float, default=0.0)
    lead_score = Column(Float, default=0.0)  # Alias for score
    priority = Column(Integer, default=5)
    
    # Call History
    call_attempts = Column(Integer, default=0)
    last_call_date = Column(DateTime)
    best_call_time = Column(DateTime)
    
    # DNC & Compliance
    dnc_status = Column(Boolean, default=False)
    dnc_date = Column(DateTime)
    consent_status = Column(Boolean, default=False)
    consent_date = Column(DateTime)
    
    # Custom Fields
    custom_fields = Column(JSON)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="leads")
    call_logs = relationship("CallLog", back_populates="lead")
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_leads_phone', 'phone'),
        Index('idx_leads_area_code', 'area_code'),
        Index('idx_leads_status', 'status'),
        Index('idx_leads_campaign_status', 'campaign_id', 'status'),
    )
    
    def __repr__(self):
        return f"<Lead(phone='{self.phone}', status='{self.status}')>"

class DIDPool(Base):
    __tablename__ = "did_pool"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(20), unique=True, nullable=False)
    
    # Geographic Information
    area_code = Column(String(3), nullable=False)
    state = Column(String(2))
    city = Column(String(100))
    
    # Status & Reputation
    status = Column(Enum(DIDStatus), default=DIDStatus.CLEAN)
    spam_score = Column(Float, default=0.0)
    reputation_score = Column(Float, default=100.0)
    
    # Usage Tracking
    calls_today = Column(Integer, default=0)
    talk_seconds_today = Column(Integer, default=0)
    total_calls = Column(Integer, default=0)
    total_talk_seconds = Column(Integer, default=0)
    
    # Twilio Information
    twilio_sid = Column(String(100))
    twilio_friendly_name = Column(String(255))
    
    # Rotation & Cooldown
    last_used = Column(DateTime)
    cooldown_until = Column(DateTime)
    quarantine_reason = Column(Text)
    
    # Cost Tracking
    purchase_cost = Column(Float, default=1.0)
    monthly_cost = Column(Float, default=1.0)
    
    # Relationships
    call_logs = relationship("CallLog", back_populates="did")
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_did_area_code', 'area_code'),
        Index('idx_did_status', 'status'),
        Index('idx_did_spam_score', 'spam_score'),
        Index('idx_did_calls_today', 'calls_today'),
    )
    
    def __repr__(self):
        return f"<DID(phone='{self.phone_number}', status='{self.status}')>"

class CallLog(Base):
    __tablename__ = "call_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"))
    did_id = Column(UUID(as_uuid=True), ForeignKey("did_pool.id"))
    
    # Call Identification
    twilio_call_sid = Column(String(100), unique=True)
    twilio_conference_sid = Column(String(100))
    
    # Call Details
    from_number = Column(String(20))
    to_number = Column(String(20))
    phone_number = Column(String(20))
    status = Column(Enum(CallStatus))
    disposition = Column(Enum(CallDisposition))
    call_status = Column(String(50))
    call_start = Column(DateTime)
    call_answered = Column(DateTime)
    
    # Call Timing
    initiated_at = Column(DateTime)
    answered_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer, default=0)
    talk_time_seconds = Column(Integer, default=0)
    
    # Call Quality Metrics
    audio_quality_score = Column(Float)  # MOS score
    jitter_ms = Column(Float)
    packet_loss_percent = Column(Float)
    latency_ms = Column(Float)
    
    # AI Conversation Metrics
    ai_response_time_ms = Column(Float)
    ai_confidence_score = Column(Float)
    conversation_turns = Column(Integer, default=0)
    transfer_requested = Column(Boolean, default=False)
    objections_count = Column(Integer, default=0)
    call_duration = Column(Integer, default=0)
    call_disposition = Column(String(50))
    
    # Transfer Information
    transfer_attempted = Column(Boolean, default=False)
    transfer_number = Column(String(20))
    transfer_time = Column(DateTime)
    transfer_failed = Column(Boolean, default=False)
    transfer_successful = Column(Boolean, default=False)
    transfer_failure_reason = Column(String(100))
    ai_disconnected_at = Column(DateTime)
    
    # Cost Information
    cost_per_minute = Column(Float)
    total_cost = Column(Float)
    
    # Recording & Transcription
    recording_url = Column(String(500))
    transcript_url = Column(String(500))
    transcript_text = Column(Text)
    
    # Advanced Analytics
    sentiment_score = Column(Float)
    intent_classification = Column(String(100))
    keywords_detected = Column(ARRAY(String))
    
    # Relationships
    campaign = relationship("Campaign", back_populates="call_logs")
    lead = relationship("Lead", back_populates="call_logs")
    did = relationship("DIDPool", back_populates="call_logs")
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_call_logs_campaign', 'campaign_id'),
        Index('idx_call_logs_lead', 'lead_id'),
        Index('idx_call_logs_did', 'did_id'),
        Index('idx_call_logs_status', 'status'),
        Index('idx_call_logs_initiated', 'initiated_at'),
        Index('idx_call_logs_twilio_sid', 'twilio_call_sid'),
    )
    
    def __repr__(self):
        return f"<CallLog(sid='{self.twilio_call_sid}', status='{self.status}')>"

# Analytics Models
class CampaignAnalytics(Base):
    __tablename__ = "campaign_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    date = Column(DateTime, nullable=False)
    
    # Call Metrics
    total_calls = Column(Integer, default=0)
    answered_calls = Column(Integer, default=0)
    completed_calls = Column(Integer, default=0)
    
    # Conversion Metrics
    transfers = Column(Integer, default=0)
    qualified_leads = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    
    # Cost Metrics
    total_cost = Column(Float, default=0.0)
    cost_per_call = Column(Float, default=0.0)
    cost_per_transfer = Column(Float, default=0.0)
    
    # Quality Metrics
    avg_call_duration = Column(Float, default=0.0)
    avg_quality_score = Column(Float, default=0.0)
    avg_ai_response_time = Column(Float, default=0.0)
    
    # Optimization Metrics
    optimal_call_time = Column(Integer)  # Hour of day
    best_area_codes = Column(ARRAY(String))
    top_performing_scripts = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_analytics_campaign_date', 'campaign_id', 'date'),
    )

class DNCRegistry(Base):
    __tablename__ = "dnc_registry"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(20), unique=True, nullable=False)
    
    # Registry Information
    registry_source = Column(String(50))  # national, state, company
    state = Column(String(2))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    registered_date = Column(DateTime)
    last_updated = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_dnc_phone', 'phone_number'),
        Index('idx_dnc_state', 'state'),
        Index('idx_dnc_active', 'is_active'),
    )

class CostOptimization(Base):
    __tablename__ = "cost_optimization"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    
    # Cost Tracking
    daily_budget = Column(Float)
    current_spend = Column(Float, default=0.0)
    projected_spend = Column(Float, default=0.0)
    
    # Optimization Metrics
    target_cost_per_call = Column(Float)
    target_cost_per_transfer = Column(Float)
    actual_cost_per_call = Column(Float)
    actual_cost_per_transfer = Column(Float)
    
    # Recommendations
    recommended_actions = Column(JSON)
    auto_pause_triggered = Column(Boolean, default=False)
    
    # Timestamps
    date = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_cost_opt_campaign_date', 'campaign_id', 'date'),
    )

class QualityScore(Base):
    __tablename__ = "quality_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_log_id = Column(UUID(as_uuid=True), ForeignKey("call_logs.id"))
    
    # Technical Quality
    audio_quality = Column(Float)  # MOS score
    network_quality = Column(Float)
    
    # Conversation Quality
    conversation_flow = Column(Float)
    ai_performance = Column(Float)
    customer_satisfaction = Column(Float)
    
    # Overall Score
    overall_score = Column(Float)
    quality_grade = Column(String(2))  # A, B, C, D, F
    
    # Improvement Recommendations
    recommendations = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_quality_call_log', 'call_log_id'),
        Index('idx_quality_overall_score', 'overall_score'),
    )

class ABTestVariant(Base):
    __tablename__ = "ab_test_variants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    
    # Variant Details
    variant_name = Column(String(100), nullable=False)
    variant_type = Column(String(50))  # script, timing, did_selection
    
    # Configuration
    config_json = Column(JSON)
    traffic_percentage = Column(Float, default=50.0)
    
    # Results
    total_calls = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    cost_per_conversion = Column(Float, default=0.0)
    
    # Test Status
    is_active = Column(Boolean, default=True)
    is_winner = Column(Boolean, default=False)
    
    # Statistical Significance
    confidence_level = Column(Float, default=0.0)
    p_value = Column(Float, default=1.0)
    
    # Timestamps
    test_start_date = Column(DateTime, default=func.now())
    test_end_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_ab_test_campaign', 'campaign_id'),
        Index('idx_ab_test_active', 'is_active'),
    )

class RealtimeMetrics(Base):
    __tablename__ = "realtime_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric Identification
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50))  # gauge, counter, histogram
    
    # Dimensions
    campaign_id = Column(UUID(as_uuid=True))
    area_code = Column(String(3))
    hour_of_day = Column(Integer)
    
    # Timestamp
    timestamp = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_metrics_name_time', 'metric_name', 'timestamp'),
        Index('idx_metrics_campaign_time', 'campaign_id', 'timestamp'),
    ) 