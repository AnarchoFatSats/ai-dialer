#!/bin/bash
# AI Voice Dialer - Simple EC2 Deployment Script
# This script deploys the AI voice dialer to a single EC2 instance
# Perfect for testing, development, or small-scale production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="ai-voice-dialer"
AWS_REGION="us-east-1"
INSTANCE_TYPE="t3.medium"  # 2 vCPUs, 4 GB RAM - good for AI workloads
KEY_NAME="ai-dialer-key"
SECURITY_GROUP="ai-dialer-sg"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check AWS credentials
check_aws_credentials() {
    print_status "Checking AWS credentials..."
    
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run:"
        echo "aws configure"
        exit 1
    fi
    
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_success "AWS credentials valid (Account: $AWS_ACCOUNT_ID)"
}

# Create key pair if it doesn't exist
create_key_pair() {
    print_status "Creating EC2 key pair..."
    
    if aws ec2 describe-key-pairs --key-names $KEY_NAME --region $AWS_REGION &> /dev/null; then
        print_warning "Key pair $KEY_NAME already exists"
    else
        aws ec2 create-key-pair \
            --key-name $KEY_NAME \
            --query 'KeyMaterial' \
            --output text \
            --region $AWS_REGION > ${KEY_NAME}.pem
        
        chmod 400 ${KEY_NAME}.pem
        print_success "Key pair created: ${KEY_NAME}.pem"
    fi
}

# Create security group
create_security_group() {
    print_status "Creating security group..."
    
    # Get default VPC ID
    VPC_ID=$(aws ec2 describe-vpcs \
        --filters "Name=isDefault,Values=true" \
        --query 'Vpcs[0].VpcId' \
        --output text \
        --region $AWS_REGION)
    
    # Create security group
    if aws ec2 describe-security-groups --group-names $SECURITY_GROUP --region $AWS_REGION &> /dev/null; then
        print_warning "Security group $SECURITY_GROUP already exists"
        SG_ID=$(aws ec2 describe-security-groups \
            --group-names $SECURITY_GROUP \
            --query 'SecurityGroups[0].GroupId' \
            --output text \
            --region $AWS_REGION)
    else
        SG_ID=$(aws ec2 create-security-group \
            --group-name $SECURITY_GROUP \
            --description "AI Voice Dialer Security Group" \
            --vpc-id $VPC_ID \
            --query 'GroupId' \
            --output text \
            --region $AWS_REGION)
        
        # Add rules
        aws ec2 authorize-security-group-ingress \
            --group-id $SG_ID \
            --protocol tcp \
            --port 22 \
            --cidr 0.0.0.0/0 \
            --region $AWS_REGION
        
        aws ec2 authorize-security-group-ingress \
            --group-id $SG_ID \
            --protocol tcp \
            --port 80 \
            --cidr 0.0.0.0/0 \
            --region $AWS_REGION
        
        aws ec2 authorize-security-group-ingress \
            --group-id $SG_ID \
            --protocol tcp \
            --port 443 \
            --cidr 0.0.0.0/0 \
            --region $AWS_REGION
        
        aws ec2 authorize-security-group-ingress \
            --group-id $SG_ID \
            --protocol tcp \
            --port 8000 \
            --cidr 0.0.0.0/0 \
            --region $AWS_REGION
        
        print_success "Security group created: $SG_ID"
    fi
}

# Create user data script
create_user_data() {
    print_status "Creating user data script..."
    
    cat > user-data.sh << 'EOF'
#!/bin/bash
# AI Voice Dialer - EC2 Setup Script

# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Git
yum install -y git

# Clone repository
cd /home/ec2-user
git clone https://github.com/contentkingpins/ai-dialer.git
cd ai-dialer

# Copy environment file
cp env.example .env

# Create directories
mkdir -p logs postgres_data redis_data

# Set permissions
chown -R ec2-user:ec2-user /home/ec2-user/ai-dialer

# Create systemd service
cat > /etc/systemd/system/ai-dialer.service << 'EOL'
[Unit]
Description=AI Voice Dialer
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/ai-dialer
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOL

# Enable and start service
systemctl daemon-reload
systemctl enable ai-dialer
systemctl start ai-dialer

# Install nginx as reverse proxy
yum install -y nginx

# Configure nginx
cat > /etc/nginx/conf.d/ai-dialer.conf << 'EOL'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOL

# Start nginx
systemctl start nginx
systemctl enable nginx

# Create setup completion marker
touch /home/ec2-user/setup-complete

echo "AI Voice Dialer setup complete!"
EOF

    print_success "User data script created"
}

# Launch EC2 instance
launch_instance() {
    print_status "Launching EC2 instance..."
    
    # Get latest Amazon Linux 2 AMI
    AMI_ID=$(aws ec2 describe-images \
        --owners amazon \
        --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
        --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
        --output text \
        --region $AWS_REGION)
    
    # Launch instance
    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id $AMI_ID \
        --instance-type $INSTANCE_TYPE \
        --key-name $KEY_NAME \
        --security-group-ids $SG_ID \
        --user-data file://user-data.sh \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$APP_NAME}]" \
        --query 'Instances[0].InstanceId' \
        --output text \
        --region $AWS_REGION)
    
    print_success "Instance launched: $INSTANCE_ID"
    
    # Wait for instance to be running
    print_status "Waiting for instance to be running..."
    aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $AWS_REGION
    
    # Get instance public IP
    PUBLIC_IP=$(aws ec2 describe-instances \
        --instance-ids $INSTANCE_ID \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text \
        --region $AWS_REGION)
    
    print_success "Instance is running at: $PUBLIC_IP"
}

# Wait for setup to complete
wait_for_setup() {
    print_status "Waiting for setup to complete (this may take 5-10 minutes)..."
    
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if ssh -i ${KEY_NAME}.pem -o StrictHostKeyChecking=no ec2-user@$PUBLIC_IP "test -f /home/ec2-user/setup-complete" &> /dev/null; then
            print_success "Setup completed successfully!"
            return 0
        fi
        
        echo -n "."
        sleep 10
        ((attempt++))
    done
    
    print_warning "Setup is taking longer than expected. You can check manually."
}

# Display connection info
display_info() {
    echo ""
    echo "======================================="
    echo "🚀 AI Voice Dialer - EC2 Deployment Complete!"
    echo "======================================="
    echo ""
    echo "📊 Application URL: http://$PUBLIC_IP"
    echo "📚 API Documentation: http://$PUBLIC_IP/docs"
    echo "🔍 Health Check: http://$PUBLIC_IP/health"
    echo ""
    echo "🔧 SSH Access:"
    echo "  ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
    echo ""
    echo "📝 Next Steps:"
    echo "1. Configure your AI service API keys:"
    echo "   ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
    echo "   cd ai-dialer"
    echo "   nano .env"
    echo "   docker-compose restart"
    echo ""
    echo "2. Point your domain to: $PUBLIC_IP"
    echo "3. Set up SSL certificate (Let's Encrypt recommended)"
    echo "4. Create your first campaign and start dialing!"
    echo ""
    echo "💰 Estimated Monthly Cost: ~$30-50 (t3.medium instance)"
    echo ""
    echo "🔧 Useful Commands:"
    echo "  • View logs: docker-compose logs -f"
    echo "  • Restart app: docker-compose restart"
    echo "  • Update app: git pull && docker-compose up -d --build"
    echo ""
}

# Main deployment function
main() {
    echo ""
    echo "🤖📞 AI Voice Dialer - Simple EC2 Deployment"
    echo "============================================="
    echo ""
    
    check_aws_credentials
    create_key_pair
    create_security_group
    create_user_data
    launch_instance
    wait_for_setup
    display_info
    
    # Cleanup
    rm -f user-data.sh
}

# Run main function
main "$@" 