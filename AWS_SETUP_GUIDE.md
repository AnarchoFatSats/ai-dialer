# AWS Infrastructure Setup Guide for AI Dialer

## Overview
This guide walks you through setting up the complete AWS infrastructure for the AI Dialer application, including RDS PostgreSQL, ElastiCache Redis, ECS Fargate, and supporting services.

## Required AWS Services

### 1. Amazon RDS (PostgreSQL)
**Purpose**: Primary database for campaigns, leads, call logs, and analytics

**Setup Steps**:
1. Go to AWS RDS Console
2. Create Database → PostgreSQL
3. Choose production template (or dev/test for development)
4. Configure:
   - DB instance identifier: `aidialer-db`
   - Master username: `postgres`
   - Master password: (secure password)
   - DB instance class: `db.t3.micro` (development) or `db.r5.large` (production)
   - Storage: 20GB (minimum), enable auto-scaling
   - VPC: Default or custom VPC
   - Subnet group: Default or custom
   - Security group: Allow port 5432 from ECS tasks
   - Database name: `aidialer`

**Security Group Rules**:
- Type: PostgreSQL
- Port: 5432
- Source: ECS Security Group or VPC CIDR

### 2. Amazon ElastiCache (Redis)
**Purpose**: Caching, session storage, and Celery message broker

**Setup Steps**:
1. Go to ElastiCache Console
2. Create Redis cluster
3. Configure:
   - Cluster name: `aidialer-redis`
   - Node type: `cache.t3.micro` (development) or `cache.r5.large` (production)
   - Number of replicas: 1 (for production)
   - Subnet group: Same as RDS
   - Security group: Allow port 6379 from ECS tasks

**Security Group Rules**:
- Type: Custom TCP
- Port: 6379
- Source: ECS Security Group or VPC CIDR

### 3. Amazon ECS Fargate
**Purpose**: Container hosting for the FastAPI application

**Setup Steps**:
1. Create ECS Cluster:
   - Cluster name: `aidialer-cluster`
   - Infrastructure: AWS Fargate (serverless)

2. Create Task Definition:
   - Family: `aidialer-task`
   - Launch type: Fargate
   - CPU: 512 (0.5 vCPU) or higher
   - Memory: 1024 MB (1 GB) or higher
   - Container definitions:
     - Name: `aidialer-app`
     - Image: `your-account.dkr.ecr.us-east-1.amazonaws.com/aidialer:latest`
     - Port mappings: 8000:8000
     - Environment variables: (from env.aws.example)

3. Create Service:
   - Service name: `aidialer-service`
   - Task definition: `aidialer-task`
   - Desired count: 1 (or more for production)
   - Load balancer: Application Load Balancer
   - Target group: HTTP 8000

### 4. Application Load Balancer (ALB)
**Purpose**: Load balancing and SSL termination

**Setup Steps**:
1. Create ALB:
   - Name: `aidialer-alb`
   - Scheme: Internet-facing
   - IP address type: IPv4
   - VPC: Same as ECS
   - Subnets: Public subnets in multiple AZs

2. Create Target Group:
   - Name: `aidialer-targets`
   - Protocol: HTTP
   - Port: 8000
   - Target type: IP
   - Health check path: `/health`

3. Configure Listener:
   - Protocol: HTTPS
   - Port: 443
   - SSL certificate: From ACM
   - Default action: Forward to target group

### 5. Amazon ECR (Container Registry)
**Purpose**: Docker image storage

**Setup Steps**:
1. Create repository: `aidialer`
2. Push your Docker image:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
   docker build -t aidialer .
   docker tag aidialer:latest your-account.dkr.ecr.us-east-1.amazonaws.com/aidialer:latest
   docker push your-account.dkr.ecr.us-east-1.amazonaws.com/aidialer:latest
   ```

### 6. AWS Certificate Manager (ACM)
**Purpose**: SSL/TLS certificates

**Setup Steps**:
1. Request certificate for your domain
2. Validate domain ownership
3. Attach to ALB listener

### 7. Amazon S3
**Purpose**: File storage for call recordings, logs, and static assets

**Setup Steps**:
1. Create bucket: `aidialer-storage-{random}`
2. Configure CORS for frontend access
3. Set up lifecycle policies for cost optimization

### 8. AWS IAM Roles and Policies
**Purpose**: Security and access control

**Required Roles**:

1. **ECS Task Execution Role**:
   - Managed policies: `AmazonECSTaskExecutionRolePolicy`
   - Custom policies: ECR access, CloudWatch logs

2. **ECS Task Role**:
   - S3 access for file uploads
   - SES access for email notifications
   - CloudWatch metrics and logs

3. **Application User** (for development):
   - Programmatic access
   - Policies: RDS access, ElastiCache access, S3 access

## Environment Configuration

### Update .env file with AWS endpoints:

```env
# Database - AWS RDS PostgreSQL
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@aidialer-db.xxxxx.us-east-1.rds.amazonaws.com:5432/aidialer
REDIS_URL=redis://aidialer-redis.xxxxx.cache.amazonaws.com:6379

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=aidialer-storage-xxxxx

# System Configuration
BASE_URL=https://your-domain.com
WEBHOOK_BASE_URL=https://your-domain.com
```

## Deployment Steps

### 1. Database Migration
```bash
# Run from your local machine or CI/CD pipeline
alembic upgrade head
```

### 2. Build and Push Docker Image
```bash
docker build -t aidialer .
docker tag aidialer:latest your-account.dkr.ecr.us-east-1.amazonaws.com/aidialer:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/aidialer:latest
```

### 3. Update ECS Service
```bash
aws ecs update-service --cluster aidialer-cluster --service aidialer-service --force-new-deployment
```

## Monitoring and Logging

### CloudWatch Integration
- Container logs automatically sent to CloudWatch
- Set up custom metrics for call volume, success rates
- Create alarms for error rates, response times

### Health Check Endpoint
The application provides `/health` endpoint for:
- Database connectivity
- Redis connectivity
- External service status

## Security Considerations

1. **Network Security**:
   - Use private subnets for RDS and ElastiCache
   - Security groups with minimal required access
   - VPC endpoints for AWS services

2. **Data Encryption**:
   - RDS encryption at rest
   - ElastiCache encryption in transit and at rest
   - S3 bucket encryption

3. **Access Control**:
   - IAM roles with least privilege
   - Rotate access keys regularly
   - Use AWS Secrets Manager for sensitive data

## Cost Optimization

1. **Right-sizing**:
   - Start with smaller instances
   - Use Reserved Instances for predictable workloads
   - Enable auto-scaling for ECS

2. **Storage**:
   - S3 lifecycle policies
   - RDS automated backups retention
   - CloudWatch log retention policies

## Troubleshooting

### Common Issues:

1. **Database Connection Failed**:
   - Check security group rules
   - Verify RDS endpoint and credentials
   - Ensure ECS tasks are in correct subnets

2. **Redis Connection Failed**:
   - Check ElastiCache security group
   - Verify cluster endpoint
   - Ensure Redis is in same VPC as ECS

3. **ECS Task Fails to Start**:
   - Check CloudWatch logs
   - Verify IAM permissions
   - Ensure Docker image is accessible

## Next Steps

1. Set up AWS infrastructure using this guide
2. Update environment variables with actual AWS endpoints
3. Deploy application to ECS Fargate
4. Configure domain and SSL certificate
5. Set up monitoring and alerting
6. Implement CI/CD pipeline for automated deployments

For questions or issues, refer to AWS documentation or contact your DevOps team. 