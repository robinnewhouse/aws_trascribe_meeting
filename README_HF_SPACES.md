# 🎙️ Meeting Transcription & AI Analysis - Hugging Face Spaces Deployment

A streamlined web application that processes audio recordings through AWS services to provide clean transcripts and AI-powered meeting insights, deployed on Hugging Face Spaces.

## 🚀 Live Demo

This app is deployed on Hugging Face Spaces and available at: [Your Space URL will be here]

## 📋 How to Deploy Your Own Copy

### 1. Create a Hugging Face Account
- Sign up at [huggingface.co](https://huggingface.co)
- Go to [Spaces](https://huggingface.co/spaces) and click "Create new Space"

### 2. Set up Your Space
- **Space name**: Choose a unique name (e.g., `your-username/meeting-transcription`)
- **License**: MIT
- **Space SDK**: Gradio
- **Hardware**: CPU Basic (free tier)
- **Visibility**: Public

### 3. Upload Your Files
Upload these files to your Space:
- `app.py` (main application)
- `requirements.txt` (dependencies)
- `parse_transcribe_output.py` (transcript parsing utility)
- `README.md` (this file)

### 4. Configure AWS Secrets in Hugging Face Spaces

**CRITICAL**: You must set up these secrets in your Hugging Face Space for the app to work:

1. Go to your Space settings
2. Click on "Repository secrets" 
3. Add the following secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ACCESS_KEY_ID` | Your AWS Access Key ID | AWS credentials for API access |
| `AWS_SECRET_ACCESS_KEY` | Your AWS Secret Access Key | AWS credentials for API access |
| `AWS_REGION` | `us-east-1` (or your preferred region) | AWS region for all services |
| `S3_BUCKET` | Your S3 bucket name | S3 bucket for audio and transcript storage |

### 5. How to Get AWS Credentials

**Option A: Create Dedicated IAM User (Recommended)**
```bash
# Create IAM user for the app
aws iam create-user --user-name transcribe-app-hf

# Create access keys
aws iam create-access-key --user-name transcribe-app-hf
```

**Option B: Use Existing AWS Credentials**
If you already have AWS credentials configured locally:
```bash
# Check your current credentials
aws configure list
```

### 6. Required AWS Permissions

Your AWS credentials need access to:
- **Amazon S3**: For storing audio files and transcripts
- **Amazon Transcribe**: For audio transcription
- **Amazon Bedrock**: For AI analysis (Claude model)

**Minimal IAM Policy:**
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
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME"
        },
        {
            "Effect": "Allow",
            "Action": [
                "transcribe:StartTranscriptionJob",
                "transcribe:GetTranscriptionJob",
                "transcribe:DeleteTranscriptionJob"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": "*"
        }
    ]
}
```

### 7. Enable Bedrock Model Access

1. Go to Amazon Bedrock console
2. Navigate to "Model access"
3. Request access to "OpenAI GPT" models or "Claude 3 Haiku"
4. Wait for approval (usually instant)

## 🎯 Using the App

1. **Upload Audio**: Drag and drop an audio file (WAV, MP3, MP4, etc.)
2. **Set Instructions**: Enter specific instructions for AI analysis
3. **Process**: Click "Process Recording" and wait for results
4. **Download**: Get clean transcript and AI analysis

## 🔧 Supported Audio Formats

- WAV, MP3, MP4/M4A, FLAC, OGG, AMR, WebM

## 🐛 Troubleshooting

### Common Issues

1. **"Access Denied" errors**: 
   - Check that your AWS credentials are correctly set in Space secrets
   - Verify IAM permissions for S3, Transcribe, and Bedrock

2. **"Model access denied"**:
   - Enable Bedrock model access in AWS console
   - Ensure your region supports the required models

3. **Space not starting**:
   - Check the build logs in your Space
   - Verify all required files are uploaded
   - Ensure requirements.txt has correct dependencies

### Getting Help

- Check your Space's build logs for specific error messages
- Verify all secrets are properly set in Space settings
- Test your AWS credentials locally first

## 🔒 Security Notes

- Your AWS credentials are stored securely in Hugging Face Spaces secrets
- Credentials are not visible in the public repository
- The app only uses minimal required AWS permissions
- Audio files and transcripts are temporarily stored in your S3 bucket

## 💡 Cost Considerations

- **Hugging Face Spaces**: Free hosting for public apps
- **AWS Transcribe**: ~$0.024 per minute of audio
- **AWS Bedrock**: Varies by model (Claude ~$0.25 per 1K tokens)
- **AWS S3**: Minimal storage costs

## 📄 License

This project is open source and available under the MIT License.
