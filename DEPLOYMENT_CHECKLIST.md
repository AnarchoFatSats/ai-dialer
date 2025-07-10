# AI Dialer AWS Deployment Checklist

## Prerequisites ✅
- [x] AWS CLI installed (v2.27.18)
- [ ] AWS CLI configured with valid credentials
- [ ] Docker installed (for building images)
- [ ] Domain name ready (optional for initial deployment)

## Phase 1: AWS Infrastructure Setup

### 1. Verify AWS Access
```bash
# Test AWS credentials
aws sts get-caller-identity

# If not configured, run:
aws configure
# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key  
# - Default region (us-east-1)
# - Default output format (json)
```

### 2. Create VPC and Networking (Optional - can use default)
```bash
# Create VPC (optional - can use default VPC)
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=aidialer-vpc}]'

# If using default VPC, get VPC ID:
aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text
```

### 3. Create Security Groups
```bash
# Create security group for RDS
aws ec2 create-security-group \
  --group-name aidialer-rds-sg \
  --description "Security group for AI Dialer RDS database" \
  --vpc-id vpc-xxxxxxxx

# Create security group for ElastiCache
aws ec2 create-security-group \
  --group-name aidialer-redis-sg \
  --description "Security group for AI Dialer Redis cache" \
  --vpc-id vpc-xxxxxxxx

# Create security group for ECS
aws ec2 create-security-group \
  --group-name aidialer-ecs-sg \
  --description "Security group for AI Dialer ECS tasks" \
  --vpc-id vpc-xxxxxxxx

# Create security group for ALB
aws ec2 create-security-group \
  --group-name aidialer-alb-sg \
  --description "Security group for AI Dialer Application Load Balancer" \
  --vpc-id vpc-xxxxxxxx
```

### 4. Configure Security Group Rules
```bash
# Allow ECS to access RDS (PostgreSQL)
aws ec2 authorize-security-group-ingress \
  --group-id sg-rds-xxxxxxxx \
  --protocol tcp \
  --port 5432 \
  --source-group sg-ecs-xxxxxxxx

# Allow ECS to access ElastiCache (Redis)
aws ec2 authorize-security-group-ingress \
  --group-id sg-redis-xxxxxxxx \
  --protocol tcp \
  --port 6379 \
  --source-group sg-ecs-xxxxxxxx

# Allow ALB to access ECS
aws ec2 authorize-security-group-ingress \
  --group-id sg-ecs-xxxxxxxx \
  --protocol tcp \
  --port 8000 \
  --source-group sg-alb-xxxxxxxx

# Allow internet to access ALB
aws ec2 authorize-security-group-ingress \
  --group-id sg-alb-xxxxxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id sg-alb-xxxxxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

### 5. Create RDS Database
```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name aidialer-db-subnet-group \
  --db-subnet-group-description "Subnet group for AI Dialer database" \
  --subnet-ids subnet-xxxxxxxx subnet-yyyyyyyy

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier aidialer-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username postgres \
  --master-user-password YourSecurePassword123! \
  --allocated-storage 20 \
  --storage-type gp2 \
  --storage-encrypted \
  --db-name aidialer \
  --vpc-security-group-ids sg-rds-xxxxxxxx \
  --db-subnet-group-name aidialer-db-subnet-group \
  --backup-retention-period 7 \
  --multi-az false \
  --publicly-accessible false
```

### 6. Create ElastiCache Redis Cluster
```bash
# Create cache subnet group
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name aidialer-cache-subnet-group \
  --cache-subnet-group-description "Subnet group for AI Dialer cache" \
  --subnet-ids subnet-xxxxxxxx subnet-yyyyyyyy

# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id aidialer-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --cache-subnet-group-name aidialer-cache-subnet-group \
  --security-group-ids sg-redis-xxxxxxxx
```

### 7. Create ECR Repository
```bash
# Create ECR repository
aws ecr create-repository --repository-name aidialer

# Get login token for Docker
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

## Phase 2: Application Deployment

### 8. Build and Push Docker Image
```bash
# Build Docker image
docker build -t aidialer .

# Tag image for ECR
docker tag aidialer:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/aidialer:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/aidialer:latest
```

### 9. Create ECS Cluster
```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name aidialer-cluster --capacity-providers FARGATE --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1
```

### 10. Create Application Load Balancer
```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name aidialer-alb \
  --subnets subnet-xxxxxxxx subnet-yyyyyyyy \
  --security-groups sg-alb-xxxxxxxx \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4

# Create target group
aws elbv2 create-target-group \
  --name aidialer-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxxxxx \
  --target-type ip \
  --health-check-path /health \
  --health-check-protocol HTTP \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/aidialer-alb/1234567890123456 \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/aidialer-targets/1234567890123456
```

### 11. Create IAM Roles
```bash
# Create task execution role
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://task-execution-assume-role-policy.json

# Attach policies to execution role
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create task role
aws iam create-role \
  --role-name aidialer-task-role \
  --assume-role-policy-document file://task-assume-role-policy.json

# Attach policies to task role (S3, SES, etc.)
aws iam attach-role-policy \
  --role-name aidialer-task-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

### 12. Create ECS Task Definition
```bash
# Register task definition (use task-definition.json)
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### 13. Create ECS Service
```bash
# Create ECS service
aws ecs create-service \
  --cluster aidialer-cluster \
  --service-name aidialer-service \
  --task-definition aidialer-task:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxxxxx,subnet-yyyyyyyy],securityGroups=[sg-ecs-xxxxxxxx],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/aidialer-targets/1234567890123456,containerName=aidialer-app,containerPort=8000
```

## Phase 3: Configuration and Testing

### 14. Update Environment Variables
```bash
# Get RDS endpoint
aws rds describe-db-instances --db-instance-identifier aidialer-db --query 'DBInstances[0].Endpoint.Address' --output text

# Get ElastiCache endpoint
aws elasticache describe-cache-clusters --cache-cluster-id aidialer-redis --show-cache-node-info --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' --output text

# Get ALB DNS name
aws elbv2 describe-load-balancers --names aidialer-alb --query 'LoadBalancers[0].DNSName' --output text
```

### 15. Database Migration
```bash
# Update .env with actual endpoints
# Run database migration
alembic upgrade head
```

### 16. Test Deployment
```bash
# Test health endpoint
curl http://your-alb-dns-name/health

# Test API endpoints
curl http://your-alb-dns-name/docs
```

## Phase 4: Domain and SSL (Optional)

### 17. Configure Domain
```bash
# Create Route 53 hosted zone (if needed)
aws route53 create-hosted-zone --name your-domain.com --caller-reference $(date +%s)

# Request SSL certificate
aws acm request-certificate --domain-name your-domain.com --validation-method DNS

# Update ALB listener to use HTTPS
aws elbv2 modify-listener \
  --listener-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/aidialer-alb/1234567890123456/1234567890123456 \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012
```

## Status Tracking

### Infrastructure Status
- [ ] VPC and networking configured
- [ ] Security groups created and configured
- [ ] RDS PostgreSQL database created
- [ ] ElastiCache Redis cluster created
- [ ] ECR repository created
- [ ] IAM roles and policies created

### Application Status
- [ ] Docker image built and pushed to ECR
- [ ] ECS cluster created
- [ ] Application Load Balancer configured
- [ ] ECS task definition created
- [ ] ECS service running
- [ ] Database migrations completed

### Testing Status
- [ ] Health endpoint responding
- [ ] API documentation accessible
- [ ] Database connectivity verified
- [ ] Redis connectivity verified
- [ ] External services configured

### Production Readiness
- [ ] Domain configured
- [ ] SSL certificate installed
- [ ] Monitoring and alerting set up
- [ ] Backup and disaster recovery configured
- [ ] Security review completed

## Troubleshooting Commands

```bash
# Check ECS service status
aws ecs describe-services --cluster aidialer-cluster --services aidialer-service

# Check ECS tasks
aws ecs list-tasks --cluster aidialer-cluster --service-name aidialer-service

# Get task logs
aws logs get-log-events --log-group-name /ecs/aidialer-task --log-stream-name ecs/aidialer-app/task-id

# Check ALB target health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/aidialer-targets/1234567890123456

# Check RDS status
aws rds describe-db-instances --db-instance-identifier aidialer-db --query 'DBInstances[0].DBInstanceStatus'

# Check ElastiCache status
aws elasticache describe-cache-clusters --cache-cluster-id aidialer-redis --query 'CacheClusters[0].CacheClusterStatus'
```

## Next Steps After Deployment

1. **Monitor Application**: Set up CloudWatch dashboards and alarms
2. **Scale as Needed**: Adjust ECS service desired count and RDS instance size
3. **Implement CI/CD**: Set up automated deployment pipeline
4. **Security Hardening**: Review and tighten security groups and IAM policies
5. **Cost Optimization**: Implement auto-scaling and reserved instances
6. **Backup Strategy**: Configure automated backups and disaster recovery

---

**Note**: Replace placeholder values (vpc-xxxxxxxx, sg-xxxxxxxx, account IDs, etc.) with actual values from your AWS environment. 