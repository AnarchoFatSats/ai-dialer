# AI Voice Dialer Deployment Guide

## Overview
This guide will walk you through deploying the AI Voice Dialer system with all AI components (Claude, Deepgram, ElevenLabs) and real-time voice calling capabilities.

## Prerequisites

### Required Accounts & API Keys
1. **Twilio Account**
   - Sign up at https://twilio.com
   - Get Account SID and Auth Token
   - Purchase phone numbers for your campaigns

2. **Anthropic (Claude) API**
   - Sign up at https://console.anthropic.com
   - Get API key for Claude 3.5 Haiku

3. **Deepgram API**
   - Sign up at https://deepgram.com
   - Get API key for Nova-2 model

4. **ElevenLabs API**
   - Sign up at https://elevenlabs.io
   - Get API key and voice ID

5. **Database**
   - PostgreSQL 14+ (local or cloud)
   - Redis (for caching and queues)

## Step 1: Environment Setup

### 1.1 Clone and Setup
```bash
# Clone repository
git clone <your-repo-url>
cd aidialer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 1.2 Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit .env with your actual values
nano .env
```

### 1.3 Required Environment Variables
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/aidialer
REDIS_URL=redis://localhost:6379

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
BASE_URL=https://your-domain.com
DOMAIN=your-domain.com

# AI Services
ANTHROPIC_API_KEY=your_anthropic_key
DEEPGRAM_API_KEY=your_deepgram_key
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB

# AI Configuration
CLAUDE_MODEL=claude-3-haiku-20240307
DEEPGRAM_MODEL=nova-2
ELEVENLABS_MODEL=eleven_turbo_v2
```

## Step 2: Database Setup

### 2.1 Create Database
```bash
# Create PostgreSQL database
createdb aidialer

# Run migrations
alembic upgrade head
```

### 2.2 Initialize Database Schema
```bash
# Create tables
python -c "
import asyncio
from app.database import init_db
asyncio.run(init_db())
"
```

## Step 3: Twilio Configuration

### 3.1 Webhook Configuration
Configure your Twilio phone numbers with these webhook URLs:

**Voice URL:** `https://your-domain.com/webhooks/twilio/voice`  
**Status Callback:** `https://your-domain.com/webhooks/twilio/call-status/{call_log_id}`

### 3.2 Media Streams Setup
Ensure your server supports WebSocket connections for real-time audio streaming:
- WebSocket endpoint: `wss://your-domain.com/ws/media-stream/{call_log_id}`
- SSL certificate required for production

## Step 4: AI Services Validation

### 4.1 Test AI Services
```bash
# Run comprehensive system tests
python test_ai_system.py
```

### 4.2 Verify API Keys
```bash
# Test individual services
python -c "
import asyncio
from app.services.ai_conversation import ai_conversation_engine
# Test calls will be made to verify connectivity
"
```

## Step 5: Development Deployment

### 5.1 Run with Docker (Recommended)
```bash
# Build and start services
docker-compose up --build

# Check logs
docker-compose logs -f app
```

### 5.2 Run Locally
```bash
# Start background services
redis-server &
postgresql &

# Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Step 6: Production Deployment

### 6.1 AWS Fargate Deployment
```bash
# Build Docker image
docker build -t aidialer .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag aidialer:latest <account>.dkr.ecr.us-east-1.amazonaws.com/aidialer:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/aidialer:latest

# Deploy to Fargate (use provided task definition)
aws ecs update-service --cluster aidialer --service aidialer-service --force-new-deployment
```

### 6.2 Load Balancer Configuration
```bash
# Configure ALB for WebSocket support
# Enable sticky sessions for media streams
# Configure health checks: /health
```

## Step 7: System Verification

### 7.1 Health Checks
```bash
# Check system health
curl https://your-domain.com/health

# Check database connectivity
curl https://your-domain.com/campaigns
```

### 7.2 Test Call Flow
1. **Create Campaign**
```bash
curl -X POST https://your-domain.com/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Campaign",
    "script_template": "Hi, this is a test call.",
    "max_concurrent_calls": 10
  }'
```

2. **Initialize DID Pool**
```bash
curl -X POST https://your-domain.com/did/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "1",
    "area_codes": ["212", "213"],
    "count_per_area": 5
  }'
```

3. **Upload Test Lead**
```bash
curl -X POST https://your-domain.com/campaigns/1/leads \
  -H "Content-Type: application/json" \
  -d '[{
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "email": "john@example.com"
  }]'
```

4. **Start Campaign**
```bash
curl -X POST https://your-domain.com/campaigns/1/start
```

5. **Initiate Test Call**
```bash
curl -X POST https://your-domain.com/calls/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "1",
    "lead_id": "1",
    "priority": 1
  }'
```

## Step 8: Monitoring Setup

### 8.1 Prometheus Metrics
```bash
# Access metrics endpoint
curl https://your-domain.com/metrics

# Configure Prometheus scraping
# Target: your-domain.com:8000/metrics
```

### 8.2 Grafana Dashboard
```bash
# Import provided dashboard
# Configure data source: Prometheus
# Dashboard ID: aidialer-dashboard.json
```

### 8.3 Real-time Monitoring
```bash
# WebSocket dashboard connection
# URL: wss://your-domain.com/ws/dashboard
```

## Step 9: Troubleshooting

### 9.1 Common Issues

**AI Service Connection Errors:**
```bash
# Check API keys
python -c "from app.config import settings; print(settings.anthropic_api_key[:10] + '...')"

# Test connectivity
curl -H "x-api-key: your_key" https://api.anthropic.com/v1/messages
```

**WebSocket Connection Issues:**
```bash
# Check SSL certificate
openssl s_client -connect your-domain.com:443

# Test WebSocket
wscat -c wss://your-domain.com/ws/media-stream/1
```

**Database Connection Issues:**
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1"

# Check Redis connection
redis-cli ping
```

### 9.2 Logs and Debugging
```bash
# Application logs
docker-compose logs -f app

# Check specific service logs
docker-compose logs -f redis
docker-compose logs -f postgres

# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG
```

## Step 10: Scaling Considerations

### 10.1 Horizontal Scaling
- Use load balancer with sticky sessions for WebSocket connections
- Scale Fargate services based on CPU/memory metrics
- Consider Redis Cluster for high availability

### 10.2 Performance Optimization
- Enable CDN for static assets
- Use connection pooling for database
- Implement proper caching strategies
- Monitor AI service latency

### 10.3 Cost Optimization
- Monitor AI service usage costs
- Implement auto-scaling policies
- Use spot instances for non-critical workloads
- Set budget alerts and auto-pause triggers

## Step 11: Security Checklist

### 11.1 API Security
- [ ] Enable HTTPS/WSS only
- [ ] Implement rate limiting
- [ ] Validate webhook signatures
- [ ] Use API keys for external services

### 11.2 Data Security
- [ ] Encrypt sensitive data at rest
- [ ] Use environment variables for secrets
- [ ] Implement proper access controls
- [ ] Regular security updates

### 11.3 Compliance
- [ ] TCPA compliance checks
- [ ] DNC scrubbing enabled
- [ ] Call recording consent
- [ ] Data retention policies

## Step 12: Backup and Recovery

### 12.1 Database Backup
```bash
# Automated backups
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore from backup
psql $DATABASE_URL < backup_20240101.sql
```

### 12.2 Configuration Backup
```bash
# Backup environment configuration
cp .env .env.backup.$(date +%Y%m%d)

# Backup Docker configuration
cp docker-compose.yml docker-compose.yml.backup
```

## Support and Maintenance

### Regular Tasks
- [ ] Monitor AI service costs and usage
- [ ] Update API keys before expiration
- [ ] Review and rotate DID pools
- [ ] Analyze call quality metrics
- [ ] Update dependencies and security patches

### Performance Monitoring
- [ ] Track AI response times (<800ms target)
- [ ] Monitor answer rates (>18% target)
- [ ] Watch transfer rates (>9% target)
- [ ] Monitor cost per transfer (<$0.14 target)

### Scaling Triggers
- [ ] CPU usage > 70%
- [ ] Memory usage > 80%
- [ ] Queue size > 1000
- [ ] Response time > 2 seconds

## Conclusion

Your AI Voice Dialer system is now ready for production use. The system includes:

✅ **Real-time AI Conversations** with Claude, Deepgram, and ElevenLabs  
✅ **Advanced Call Orchestration** with intelligent routing  
✅ **DID Reputation Management** with automated rotation  
✅ **Comprehensive Analytics** with predictive insights  
✅ **Cost Optimization** with budget protection  
✅ **TCPA Compliance** with DNC scrubbing  

For additional support, refer to the API documentation at `/docs` or contact your technical team. 