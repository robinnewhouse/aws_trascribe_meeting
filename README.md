---
title: Meeting Transcription & AI Analysis
emoji: 🎙️
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: "5.47.0"
app_file: app.py
pinned: false
---

# 🎙️ Meeting Transcription & AI Analysis App

A streamlined web application that processes audio recordings through AWS services to provide clean transcripts and AI-powered meeting insights. **No Lambda functions required** - everything runs directly in the Gradio app!

## 🚀 Features

- **Audio Upload**: Simple drag-and-drop audio file upload
- **Direct Transcription**: Uses Amazon Transcribe with speaker identification (no Lambda needed)
- **Clean Transcript**: Parses raw transcription data into readable conversation format
- **AI Analysis**: Leverages Amazon Bedrock (Claude) for meeting summaries and insights
- **Custom Instructions**: Tailor AI analysis based on your specific needs
- **Lightning Fast Setup**: Uses uv package manager for 10-100x faster dependency installation
- **Simplified Architecture**: Direct AWS service integration without serverless complexity

## 📋 Prerequisites

1. **AWS Account** with the following services enabled:
   - Amazon S3
   - Amazon Transcribe
   - Amazon Bedrock (with Claude model access)

2. **AWS CLI** configured with appropriate credentials
3. **Python 3.10+**
4. **uv package manager**

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
# Install uv if you haven't already
pip install uv

# Install dependencies with uv
uv sync
```

### 2. Configure AWS

**Option A: Use Existing AWS Credentials (Recommended for Development)**
If you already have AWS credentials configured on your machine:
```bash
aws configure
```

**Option B: Create Dedicated IAM User (Recommended for Production)**
Create a dedicated IAM user for the transcription app:

```bash
# Create IAM user
aws iam create-user --user-name transcribe-app

# Create access key for the user
aws iam create-access-key --user-name transcribe-app
```

The command will return access keys. Set them as environment variables:

```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1
```

**Option C: Use Admin Credentials (Quick Development Setup)**
For quick development/testing, you can use your existing admin credentials:
```bash
aws configure
```

### 3. Set Up AWS Resources

**Option A: Automated Setup (Recommended)**
```bash
./deploy.sh
```

This script will:
- Create a unique S3 bucket for your account
- Generate a personalized IAM trust policy
- Create a `.env` file with your bucket configuration

**Option B: Manual Setup**
```bash
# Create S3 bucket (replace with your preferred name)
aws s3 mb s3://your-transcription-bucket --region us-east-1

# Create .env file
cat > .env << EOF
AWS_REGION=us-east-1
S3_BUCKET=your-transcription-bucket
EOF
```

### 4. Set Up IAM Permissions

**Option A: Create Dedicated IAM User (Recommended for Production)**
After running `./deploy.sh`, create a dedicated IAM user with minimal permissions:

```bash
# Create IAM user
aws iam create-user --user-name transcribe-app

# Create policy from generated trust policy
aws iam create-policy --policy-name TranscribeS3LeastPriv --policy-document file://trust-policy-YOUR_BUCKET_NAME.json

# Get policy ARN and attach to user
POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='TranscribeS3LeastPriv'].Arn" --output text)
aws iam attach-user-policy --user-name transcribe-app --policy-arn "$POLICY_ARN"

# Create access keys
aws iam create-access-key --user-name transcribe-app
```

Then set the environment variables with the returned access keys:
```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1
```

**Option B: Use Existing Admin Credentials (Fine for Development)**
If you already have AWS credentials configured with admin access, you can use those directly. Just make sure they have permissions for S3, Transcribe, and Bedrock.

**Option C: Attach Policy to Existing User/Role**
```bash
# For IAM users
aws iam put-user-policy --user-name YOUR_USERNAME --policy-name TranscriptionAppPolicy --policy-document file://trust-policy-YOUR_BUCKET_NAME.json

# For IAM roles
aws iam put-role-policy --role-name YOUR_ROLE_NAME --policy-name TranscriptionAppPolicy --policy-document file://trust-policy-YOUR_BUCKET_NAME.json
```

**Template Trust Policy**
The `trust-policy.json` file contains a template with `YOUR_BUCKET_NAME` placeholder. Replace this with your actual bucket name before applying to IAM.

### 5. Configure Environment Variables

The `deploy.sh` script automatically creates a `.env` file with your bucket configuration, or you can create one manually:

```bash
# Create .env file
cat > .env << EOF
AWS_REGION=us-east-1
S3_BUCKET=your-transcription-bucket
EOF
```

**If using dedicated IAM user (Option A above):**
```bash
# Add access keys to .env file
cat >> .env << EOF
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
EOF
```

**If using existing admin credentials (Option B above):**
Your existing AWS credentials will be used automatically. No additional environment variables needed.

**Or set environment variables directly:**
```bash
export AWS_REGION=us-east-1
export S3_BUCKET=your-transcription-bucket
# Only needed if using dedicated IAM user
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
```

### 6. Enable Bedrock Model Access

1. Go to Amazon Bedrock console
2. Navigate to "Model access"
3. Request access to "Claude 3 Haiku" model
4. Wait for approval (usually instant for most regions)

## 🎯 Running the Application

### Local Development

**Quick Start (Recommended)**
```bash
python start.py
```

**Manual Start**
```bash
python app.py
```

The app will be available at `http://localhost:7860`

### Production Deployment

For production deployment, consider using:

1. **AWS ECS/Fargate** with the Gradio app containerized
2. **EC2** with a reverse proxy setup
3. **AWS App Runner** for containerized deployment

## 📁 Project Structure

```
├── app.py                     # Main Gradio application with direct AWS integration
├── lambda_function.py         # Legacy Lambda function (optional, not used)
├── parse_transcribe_output.py # Transcript parsing utility
├── pyproject.toml            # Python dependencies and project config
├── uv.lock                   # Dependency lockfile for reproducible builds
├── start.py                  # Quick start script with auto-setup
├── deploy.sh                 # Automated AWS setup script (S3 bucket + IAM policy generation)
├── trust-policy.json         # Template IAM trust policy with placeholder bucket name
├── README.md                 # This file
└── .env                      # Environment variables (auto-created by deploy.sh)
```

## 🔧 Usage

1. **Upload Audio**: Drag and drop or click to upload an audio file (supports WAV, MP3, MP4, etc.)

2. **Set Instructions**: Enter specific instructions for the AI analysis (e.g., "Focus on action items and decisions")

3. **Process**: Click "Process Recording" and wait for:
   - File upload to S3
   - Direct transcription job processing
   - AI analysis generation

4. **Review Results**: 
   - Clean transcript with speaker labels
   - AI-generated summary and insights

## 🎵 Supported Audio Formats

- WAV
- MP3
- MP4/M4A
- FLAC
- OGG
- AMR
- WebM

## ⚙️ Configuration Options

### Transcription Timeouts

The app polls for transcription completion with these settings:
- Maximum wait time: 10 minutes (600 seconds)
- Poll interval: 10 seconds
- Automatic cleanup of completed transcription jobs

### Transcribe Settings

In `app.py`, you can modify the transcription settings:
- `MaxSpeakerLabels`: Number of expected speakers (default: 10)
- `LanguageCode`: Language for transcription (default: 'en-US')
- Audio quality and format settings

### Bedrock Model

The app uses Claude 3 Haiku by default. To use a different model, update the `modelId` in the `get_bedrock_analysis` function in `app.py`.

## 🐛 Troubleshooting

### Common Issues

1. **"Access Denied" errors**: Check IAM permissions for S3, Transcribe, and Bedrock
2. **Bedrock model access**: Ensure model access is granted in Bedrock console
3. **Transcription timeouts**: For very long files, consider chunking or increasing timeout
4. **Large file uploads**: The app handles files up to reasonable sizes; very large files may need optimization

### Debug Mode

Set `DEBUG=True` in the environment to enable verbose logging.

## 💡 Future Enhancements

- Support for multiple languages
- Real-time transcription
- Integration with meeting platforms (Zoom, Teams)
- Advanced speaker identification
- Meeting templates and custom prompts
- Export options (PDF, Word, etc.)

## 📄 License

This project is open source and available under the MIT License.
