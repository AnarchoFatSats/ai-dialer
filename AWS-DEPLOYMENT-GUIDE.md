# 🚀 AWS Deployment Guide for AI Voice Dialer

Deploy your AI Voice Dialer to AWS for enterprise-grade scalability, reliability, and performance.

## 🎯 Deployment Options

### 1. 🚀 **ECS Fargate (Recommended for Production)**
- **Best for**: Production workloads, high availability, auto-scaling
- **Cost**: $100-500/month (based on usage)
- **Setup time**: 20-30 minutes
- **Scalability**: 1-1000+ concurrent calls
- **Maintenance**: Minimal (serverless)

### 2. 🏗️ **Single EC2 Instance (Best for Testing)**
- **Best for**: Development, testing, small-scale production
- **Cost**: $30-50/month
- **Setup time**: 10-15 minutes
- **Scalability**: 1-50 concurrent calls
- **Maintenance**: Moderate

### 3. 🏢 **Multi-EC2 with Load Balancer**
- **Best for**: Custom configurations, cost optimization
- **Cost**: $80-200/month
- **Setup time**: 45-60 minutes
- **Scalability**: 1-200 concurrent calls
- **Maintenance**: High

## 📋 Prerequisites

### 1. AWS Account Setup
```bash
# Create AWS account at https://aws.amazon.com/
# Configure billing alerts
# Set up IAM user with programmatic access
```

### 2. Install AWS CLI
```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Windows
# Download from https://awscli.amazonaws.com/AWSCLIV2.msi
```

### 3. Configure AWS CLI
```bash
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key
# Enter your preferred region (e.g., us-east-1)
# Enter output format (json)
```

### 4. Install Additional Tools
```bash
# Install Terraform (for ECS deployment)
brew install terraform

# Install Docker
brew install docker

# Verify installations
aws --version
terraform --version
docker --version
```

## 🚀 Option 1: ECS Fargate Deployment (Recommended)

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Production Architecture                  │
├─────────────────────────────────────────────────────────────┤
│  Internet Gateway → ALB → ECS Fargate (2-10 instances)    │
│  ├── RDS PostgreSQL (Multi-AZ)                            │
│  ├── ElastiCache Redis (Multi-AZ)                         │
│  ├── S3 Bucket (Call recordings)                          │
│  └── CloudWatch (Monitoring & Logs)                       │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step Deployment

#### 1. Prepare Environment
```bash
# Clone repository
git clone https://github.com/contentkingpins/ai-dialer.git
cd ai-dialer

# Configure environment variables
cp env.example .env
nano .env  # Add your API keys
```

#### 2. Deploy Infrastructure
```bash
# Run automated deployment
./deploy-to-aws.sh --first-time

# Or manually with Terraform
terraform init
terraform plan
terraform apply
```

#### 3. Configure Domain (Optional)
```bash
# Get ALB DNS from output
ALB_DNS=$(terraform output -raw load_balancer_dns)

# Point your domain to ALB_DNS
# Example: api.yourdomain.com CNAME ALB_DNS
```

#### 4. Set Up SSL Certificate
```bash
# Request SSL certificate through AWS Certificate Manager
aws acm request-certificate \
    --domain-name api.yourdomain.com \
    --validation-method DNS \
    --region us-east-1
```

### Expected Costs (Monthly)
- **ECS Fargate**: $50-200 (2-10 instances)
- **RDS PostgreSQL**: $25-100 (db.t3.micro to db.r5.large)
- **ElastiCache Redis**: $20-80 (cache.t3.micro to cache.r5.large)
- **Application Load Balancer**: $20
- **Data Transfer**: $10-50
- **S3 Storage**: $5-20
- **CloudWatch**: $5-15
- **Total**: $135-485/month

## 🏗️ Option 2: Simple EC2 Deployment

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Simple Architecture                      │
├─────────────────────────────────────────────────────────────┤
│  Internet Gateway → EC2 Instance (t3.medium)              │
│  ├── Docker Compose (App + PostgreSQL + Redis)           │
│  ├── Nginx (Reverse Proxy)                               │
│  └── Local Storage (Call recordings)                      │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step Deployment

#### 1. Quick Deploy
```bash
# Run automated deployment
./deploy-ec2-simple.sh

# Wait for completion (5-10 minutes)
```

#### 2. Manual Configuration
```bash
# Connect to your instance
ssh -i ai-dialer-key.pem ec2-user@YOUR_PUBLIC_IP

# Configure environment
cd ai-dialer
nano .env

# Add your API keys:
ANTHROPIC_API_KEY=sk-ant-...
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...

# Restart services
docker-compose restart
```

#### 3. Verify Deployment
```bash
# Check application status
curl http://YOUR_PUBLIC_IP/health

# View logs
docker-compose logs -f app

# Access API documentation
# Visit: http://YOUR_PUBLIC_IP/docs
```

### Expected Costs (Monthly)
- **EC2 Instance (t3.medium)**: $30-35
- **EBS Storage**: $8-15
- **Data Transfer**: $5-20
- **Total**: $43-70/month

## 🏢 Option 3: Multi-EC2 with Load Balancer

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Scalable Architecture                    │
├─────────────────────────────────────────────────────────────┤
│  Internet Gateway → ALB → EC2 Instances (2-5)             │
│  ├── RDS PostgreSQL (Separate instance)                   │
│  ├── ElastiCache Redis (Separate instance)                │
│  ├── S3 Bucket (Call recordings)                          │
│  └── Auto Scaling Group                                   │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step Deployment

#### 1. Create Launch Template
```bash
# Create launch template for auto scaling
aws ec2 create-launch-template \
    --launch-template-name ai-dialer-template \
    --launch-template-data file://launch-template.json
```

#### 2. Set Up Auto Scaling
```bash
# Create auto scaling group
aws autoscaling create-auto-scaling-group \
    --auto-scaling-group-name ai-dialer-asg \
    --launch-template LaunchTemplateName=ai-dialer-template,Version=1 \
    --min-size 2 \
    --max-size 5 \
    --desired-capacity 2 \
    --target-group-arns arn:aws:elasticloadbalancing:...
```

#### 3. Configure Load Balancer
```bash
# Create application load balancer
aws elbv2 create-load-balancer \
    --name ai-dialer-alb \
    --subnets subnet-12345 subnet-67890 \
    --security-groups sg-12345
```

### Expected Costs (Monthly)
- **EC2 Instances (2x t3.medium)**: $60-70
- **Application Load Balancer**: $20
- **RDS PostgreSQL**: $25-50
- **ElastiCache Redis**: $20-40
- **S3 Storage**: $5-15
- **Data Transfer**: $10-30
- **Total**: $140-225/month

## 🔧 Configuration Guide

### Environment Variables
```env
# Core Application
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379

# AI Services
ANTHROPIC_API_KEY=sk-ant-...
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...

# Twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890

# Webhooks
WEBHOOK_BASE_URL=https://api.yourdomain.com

# Cost & Budget
MAX_COST_PER_MINUTE=0.025
MAX_DAILY_BUDGET=1000.00
COST_ALERT_THRESHOLD=0.80

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
```

### SSL Certificate Setup
```bash
# Install Certbot
sudo yum install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Monitoring Setup
```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
sudo rpm -U ./amazon-cloudwatch-agent.rpm

# Configure monitoring
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

## 📊 Performance Optimization

### Database Optimization
```sql
-- Optimize PostgreSQL for AI workloads
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
SELECT pg_reload_conf();
```

### Redis Optimization
```bash
# Redis configuration for AI workloads
echo "maxmemory 1gb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf
echo "save 900 1" >> /etc/redis/redis.conf
echo "save 300 10" >> /etc/redis/redis.conf
echo "save 60 10000" >> /etc/redis/redis.conf
systemctl restart redis
```

### Application Optimization
```python
# Optimize uvicorn for production
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-log \
    --loop uvloop
```

## 🔍 Monitoring & Troubleshooting

### CloudWatch Metrics
```bash
# Key metrics to monitor
- ECS CPU/Memory utilization
- RDS connections/queries
- ALB request count/latency
- Custom: Call success rate, AI response time
```

### Log Analysis
```bash
# View ECS logs
aws logs tail /ecs/ai-voice-dialer --follow

# View application logs
docker-compose logs -f app

# Search for errors
aws logs filter-log-events \
    --log-group-name /ecs/ai-voice-dialer \
    --filter-pattern "ERROR"
```

### Health Checks
```bash
# Application health
curl http://YOUR_DOMAIN/health

# Database health
curl http://YOUR_DOMAIN/health/db

# Redis health
curl http://YOUR_DOMAIN/health/redis

# AI services health
curl http://YOUR_DOMAIN/health/ai
```

## 🛡️ Security Best Practices

### Network Security
```bash
# Restrict database access
aws ec2 authorize-security-group-ingress \
    --group-id sg-database \
    --protocol tcp \
    --port 5432 \
    --source-group sg-application

# Use VPC endpoints for AWS services
aws ec2 create-vpc-endpoint \
    --vpc-id vpc-12345 \
    --service-name com.amazonaws.region.s3 \
    --route-table-ids rtb-12345
```

### Data Encryption
```bash
# Encrypt RDS at rest
aws rds create-db-instance \
    --storage-encrypted \
    --kms-key-id arn:aws:kms:region:account:key/key-id

# Encrypt EBS volumes
aws ec2 create-volume \
    --encrypted \
    --kms-key-id arn:aws:kms:region:account:key/key-id
```

### IAM Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::ai-dialer-recordings/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## 🔄 Backup & Recovery

### Database Backups
```bash
# Automated RDS backups
aws rds modify-db-instance \
    --db-instance-identifier ai-dialer-db \
    --backup-retention-period 7 \
    --apply-immediately

# Manual snapshot
aws rds create-db-snapshot \
    --db-instance-identifier ai-dialer-db \
    --db-snapshot-identifier ai-dialer-snapshot-$(date +%Y%m%d)
```

### Application Backups
```bash
# Backup environment configuration
tar -czf ai-dialer-config-$(date +%Y%m%d).tar.gz \
    .env docker-compose.yml

# Upload to S3
aws s3 cp ai-dialer-config-$(date +%Y%m%d).tar.gz \
    s3://ai-dialer-backups/
```

## 🚀 Scaling Strategies

### Horizontal Scaling
```bash
# Scale ECS service
aws ecs update-service \
    --cluster ai-dialer-cluster \
    --service ai-dialer-service \
    --desired-count 5

# Scale EC2 auto scaling group
aws autoscaling update-auto-scaling-group \
    --auto-scaling-group-name ai-dialer-asg \
    --desired-capacity 3
```

### Vertical Scaling
```bash
# Scale RDS instance
aws rds modify-db-instance \
    --db-instance-identifier ai-dialer-db \
    --db-instance-class db.t3.large \
    --apply-immediately

# Scale Redis cluster
aws elasticache modify-replication-group \
    --replication-group-id ai-dialer-redis \
    --node-group-id 0001 \
    --cache-node-type cache.t3.medium
```

## 📞 Support & Maintenance

### Regular Maintenance Tasks
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update Docker images
docker-compose pull
docker-compose up -d

# Database maintenance
psql -c "VACUUM ANALYZE;"
psql -c "REINDEX DATABASE aidialer;"

# Log rotation
logrotate -f /etc/logrotate.d/ai-dialer
```

### Monitoring Alerts
```bash
# Set up CloudWatch alarms
aws cloudwatch put-metric-alarm \
    --alarm-name "AI-Dialer-High-CPU" \
    --alarm-description "High CPU usage" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold
```

## 📚 Additional Resources

### Documentation
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

### Community
- [AWS Community Forums](https://forums.aws.amazon.com/)
- [AI Voice Dialer GitHub Issues](https://github.com/contentkingpins/ai-dialer/issues)
- [Discord Community](https://discord.gg/your-invite)

### Professional Support
- **AWS Support**: Consider Business or Enterprise support plans
- **Professional Services**: Available for custom implementations
- **Consulting**: Architecture review and optimization services

---

🎉 **Ready to deploy your AI Voice Dialer to AWS!** Choose the deployment option that best fits your needs and follow the step-by-step guide above. 