from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON, Enum, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum
from datetime import datetime

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

    # AWS Connect Configuration
    aws_contact_flow_id = Column(String(100))

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

    # AWS Connect Information
    aws_phone_number_id = Column(String(100))
    aws_phone_number_arn = Column(String(500))

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
    aws_contact_id = Column(String(100), unique=True)
    aws_contact_flow_id = Column(String(100))

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
        Index('idx_call_logs_aws_contact_id', 'aws_contact_id'),
    )

    def __repr__(self):
        return f"<CallLog(contact_id='{self.aws_contact_id}', status='{self.status}')>"

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

# Multi-Agent AI Dialer System Models


class AgentPool(Base):
    """Virtual agents for human-like dialing patterns"""
    __tablename__ = "agent_pools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)  # e.g., "East Coast Sales Team"
    # e.g., "east_coast", "west_coast"
    region = Column(String(50), nullable=False)

    # AI Personality Configuration
    # Voice, conversation style, etc.
    personality_config = Column(JSON, nullable=False)

    # Operational Schedule
    # {"start": "09:00", "end": "17:00", "timezone": "EST"}
    active_hours = Column(JSON, nullable=False)

    # Dialing Behavior
    # {"max_attempts": 3, "rest_hours": 4, "velocity": "moderate"}
    dialing_pattern = Column(JSON, nullable=False)

    # Performance Metrics
    success_rate = Column(Float, default=0.0)
    answer_rate = Column(Float, default=0.0)
    reputation_score = Column(Float, default=5.0)  # 1-10 scale

    # Status
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    agent_numbers = relationship("AgentNumber", back_populates="agent_pool")
    call_logs = relationship("CallLog", back_populates="agent_pool")

    def __repr__(self):
        return f"<AgentPool(name='{self.name}', region='{self.region}', active={self.is_active})>"


class AgentNumber(Base):
    """Phone numbers assigned to specific agents"""
    __tablename__ = "agent_numbers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(
        UUID(
            as_uuid=True),
        ForeignKey("agent_pools.id"),
        nullable=False)
    did_id = Column(
        UUID(
            as_uuid=True),
        ForeignKey("did_pool.id"),
        nullable=False)

    # Assignment Details
    assigned_at = Column(DateTime, default=datetime.utcnow)
    # Primary number for this agent
    is_primary = Column(Boolean, default=False)

    # Performance Tracking
    call_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    answer_rate = Column(Float, default=0.0)
    spam_score = Column(Float, default=0.0)  # 0-10 scale, 0 = clean

    # Health Status
    health_score = Column(Float, default=10.0)  # 1-10 scale, 10 = excellent
    is_blocked = Column(Boolean, default=False)
    blocked_reason = Column(String(255), nullable=True)
    blocked_at = Column(DateTime, nullable=True)

    # Usage Stats
    last_used_at = Column(DateTime, nullable=True)
    calls_today = Column(Integer, default=0)
    calls_this_week = Column(Integer, default=0)

    # Relationships
    agent_pool = relationship("AgentPool", back_populates="agent_numbers")
    did = relationship("DIDPool", back_populates="agent_assignments")

    def __repr__(self):
        return f"<AgentNumber(agent_id={self.agent_id}, did_id={self.did_id}, health={self.health_score})>"


class CallRoutingRule(Base):
    """Dynamic routing rules for intelligent call distribution"""
    __tablename__ = "call_routing_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Rule Configuration
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=1)  # Higher = more important

    # Rule Conditions
    # {"area_code": "212", "time_of_day": "business_hours"}
    conditions = Column(JSON, nullable=False)

    # Routing Actions
    # {"preferred_agents": ["agent_1"], "backup_agents": ["agent_2"]}
    routing_config = Column(JSON, nullable=False)

    # Performance Tracking
    times_used = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CallRoutingRule(name='{self.name}', priority={self.priority}, active={self.is_active})>"


class NumberReputation(Base):
    """Phone number reputation monitoring and spam detection"""
    __tablename__ = "number_reputation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    did_id = Column(
        UUID(
            as_uuid=True),
        ForeignKey("did_pool.id"),
        nullable=False)

    # Reputation Data
    # "verizon", "att", "tmobile", etc.
    carrier = Column(String(50), nullable=False)
    reputation_score = Column(Float, default=5.0)  # 1-10 scale
    spam_likelihood = Column(Float, default=0.0)  # 0-1 scale

    # Status Labels
    is_spam_flagged = Column(Boolean, default=False)
    is_scam_flagged = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)

    # Label Details
    # "Spam Likely", "Scam Likely", etc.
    current_label = Column(String(100), nullable=True)
    # "numeracle", "tns", "carrier"
    label_source = Column(String(50), nullable=True)

    # Monitoring Service Data
    # ID from monitoring service
    external_id = Column(String(100), nullable=True)
    last_checked_at = Column(DateTime, default=datetime.utcnow)

    # Historical Tracking
    # List of historical reputation scores
    reputation_history = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow)

    # Relationships
    did = relationship("DIDPool", back_populates="reputation_records")

    def __repr__(self):
        return f"<NumberReputation(did_id={self.did_id}, score={self.reputation_score}, spam={self.is_spam_flagged})>"


class CNAMRegistration(Base):
    """Caller ID (CNAM) registration and management"""
    __tablename__ = "cnam_registrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    did_id = Column(
        UUID(
            as_uuid=True),
        ForeignKey("did_pool.id"),
        nullable=False)

    # CNAM Details
    display_name = Column(String(15), nullable=False)  # 15 char limit for CNAM
    business_name = Column(String(100), nullable=False)
    registration_type = Column(String(50),
                               default="business")  # "business", "individual"

    # Registration Status
    is_registered = Column(Boolean, default=False)
    registration_date = Column(DateTime, nullable=True)

    # Carrier Registration Status
    # {"verizon": "approved", "att": "pending"}
    carrier_registrations = Column(JSON, default=dict)

    # Verification Details
    verification_code = Column(String(20), nullable=True)
    # "pending", "verified", "failed"
    verification_status = Column(String(20), default="pending")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow)

    # Relationships
    did = relationship("DIDPool", back_populates="cnam_registration")

    def __repr__(self):
        return f"<CNAMRegistration(did_id={self.did_id}, name='{self.display_name}', verified={self.is_registered})>"


class ComplianceTracking(Base):
    """TCPA and DNC compliance tracking"""
    __tablename__ = "compliance_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(20), nullable=False)

    # DNC Status
    is_on_dnc_federal = Column(Boolean, default=False)
    is_on_dnc_state = Column(Boolean, default=False)
    dnc_states = Column(JSON, default=list)  # List of state DNC registrations

    # Consent Management
    has_consent = Column(Boolean, default=False)
    # "express", "implied", "written"
    consent_type = Column(String(50), nullable=True)
    consent_date = Column(DateTime, nullable=True)
    # Where consent was obtained
    consent_source = Column(String(100), nullable=True)

    # Opt-out Management
    has_opted_out = Column(Boolean, default=False)
    opt_out_date = Column(DateTime, nullable=True)
    # "verbal", "text", "email"
    opt_out_method = Column(String(50), nullable=True)

    # Complaint History
    complaint_count = Column(Integer, default=0)
    last_complaint_date = Column(DateTime, nullable=True)
    complaint_details = Column(JSON, default=list)  # List of complaint records

    # Last Contact
    last_contact_date = Column(DateTime, nullable=True)
    # "answered", "no_answer", "busy"
    last_contact_result = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ComplianceTracking(phone={self.phone_number}, consent={self.has_consent}, dnc={self.is_on_dnc_federal})>"


# Update existing models to support multi-agent system

# Add agent_pool relationship to CallLog
CallLog.agent_pool_id = Column(
    UUID(
        as_uuid=True),
    ForeignKey("agent_pools.id"),
    nullable=True)
CallLog.agent_pool = relationship("AgentPool", back_populates="call_logs")

# Add agent assignments relationship to DIDPool
DIDPool.agent_assignments = relationship("AgentNumber", back_populates="did")
DIDPool.reputation_records = relationship(
    "NumberReputation", back_populates="did")
DIDPool.cnam_registration = relationship(
    "CNAMRegistration",
    back_populates="did",
    uselist=False)

# Add multi-agent fields to Campaign
# List of agent pool IDs to use
Campaign.agent_pool_ids = Column(JSON, default=list)
# "round_robin", "weighted", "intelligent"
Campaign.routing_strategy = Column(String(50), default="round_robin")
# How many numbers to use per campaign
Campaign.number_pool_size = Column(Integer, default=20)
