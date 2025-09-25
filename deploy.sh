#!/bin/bash

# Meeting Transcription App Deployment Script  
# This script sets up AWS resources (S3 bucket and basic IAM permissions)

set -e

# Configuration
BUCKET_PREFIX="transcription-app"
REGION=$(aws configure get region || echo "us-east-1")

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

# Generate personalized trust policy
echo -e "${YELLOW}📝 Generating personalized trust policy...${NC}"
sed "s/YOUR_BUCKET_NAME/${BUCKET_NAME}/g" trust-policy.json > trust-policy-${BUCKET_NAME}.json

echo -e "${GREEN}✅ Trust policy created: trust-policy-${BUCKET_NAME}.json${NC}"

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
echo "- Trust Policy: trust-policy-${BUCKET_NAME}.json"
echo ""
echo -e "${YELLOW}🔐 IAM Setup Options:${NC}"
echo ""
echo -e "${YELLOW}Option 1: Create dedicated IAM user (Recommended for production)${NC}"
echo "# Create IAM user"
echo "aws iam create-user --user-name transcribe-app"
echo ""
echo "# Create managed policy"
echo "aws iam create-policy --policy-name TranscribeAppPolicy --policy-document file://trust-policy-${BUCKET_NAME}.json"
echo ""
echo "# Attach managed policy to user"
echo "POLICY_ARN=\$(aws iam list-policies --query \"Policies[?PolicyName=='TranscribeAppPolicy'].Arn\" --output text)"
echo "aws iam attach-user-policy --user-name transcribe-app --policy-arn \"\$POLICY_ARN\""
echo ""
echo "# Create access keys"
echo "aws iam create-access-key --user-name transcribe-app"
echo ""
echo "Then add the access keys to your .env file:"
echo "echo 'AWS_ACCESS_KEY_ID=AKIA...' >> .env"
echo "echo 'AWS_SECRET_ACCESS_KEY=...' >> .env"
echo ""
echo "Or set environment variables directly:"
echo "export AWS_ACCESS_KEY_ID=AKIA..."
echo "export AWS_SECRET_ACCESS_KEY=..."
echo "export AWS_REGION=${REGION}"
echo ""
echo -e "${YELLOW}Option 2: Use existing admin credentials (Fine for development)${NC}"
echo "If you already have AWS credentials configured with admin access, you can use those."
echo "Just make sure they have permissions for S3, Transcribe, and Bedrock."
echo ""
echo -e "${YELLOW}Option 3: Attach policy to existing user/role${NC}"
echo "# Create managed policy first"
echo "aws iam create-policy --policy-name TranscribeAppPolicy --policy-document file://trust-policy-${BUCKET_NAME}.json"
echo "POLICY_ARN=\$(aws iam list-policies --query \"Policies[?PolicyName=='TranscribeAppPolicy'].Arn\" --output text)"
echo ""
echo "# Then attach to existing user or role"
echo "aws iam attach-user-policy --user-name YOUR_USERNAME --policy-arn \"\$POLICY_ARN\""
echo "# OR for roles:"
echo "aws iam attach-role-policy --role-name YOUR_ROLE_NAME --policy-arn \"\$POLICY_ARN\""
echo ""
echo -e "${GREEN}🌐 Application will be available at: http://localhost:7860${NC}"
