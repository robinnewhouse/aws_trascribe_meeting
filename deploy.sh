#!/bin/bash

# Meeting Transcription App Deployment Script  
# This script sets up AWS resources (S3 bucket and basic IAM permissions)

set -e

# Configuration
BUCKET_PREFIX="transcription-app"
REGION="us-east-1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Meeting Transcription App Deployment${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ Using AWS Account: ${ACCOUNT_ID}${NC}"

# Create unique bucket name
BUCKET_NAME="${BUCKET_PREFIX}-${ACCOUNT_ID}-${REGION}"
echo -e "${YELLOW}📦 Bucket name: ${BUCKET_NAME}${NC}"

# Create S3 bucket
echo -e "${YELLOW}📦 Creating S3 bucket...${NC}"
if aws s3 mb "s3://${BUCKET_NAME}" --region "${REGION}" 2>/dev/null; then
    echo -e "${GREEN}✅ S3 bucket created successfully${NC}"
else
    echo -e "${YELLOW}⚠️  S3 bucket already exists or creation failed${NC}"
fi

echo -e "${GREEN}✅ S3 bucket setup completed${NC}"
echo -e "${YELLOW}ℹ️  Note: Your AWS credentials need permissions for S3, Transcribe, and Bedrock${NC}"

# Create .env file
echo -e "${YELLOW}📝 Creating .env file...${NC}"
cat > .env << EOF
AWS_REGION=${REGION}
S3_BUCKET=${BUCKET_NAME}
EOF

echo -e "${GREEN}✅ .env file created${NC}"

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Install Python dependencies: uv sync"
echo "2. Enable Bedrock model access in AWS Console (Claude 3 Haiku)"
echo "3. Ensure your AWS credentials have permissions for:"
echo "   - Amazon S3 (read/write)"
echo "   - Amazon Transcribe (full access)"
echo "   - Amazon Bedrock (invoke model)"
echo "4. Run the application: python start.py (or python app.py)"
echo ""
echo -e "${YELLOW}📊 Resources created:${NC}"
echo "- S3 Bucket: ${BUCKET_NAME}"
echo ""
echo -e "${GREEN}🌐 Application will be available at: http://localhost:7860${NC}"
