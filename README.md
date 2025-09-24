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

Set up your AWS credentials (if not already done):
```bash
aws configure
```

### 3. Set Up AWS Resources

**Option A: Automated Setup (Recommended)**
```bash
./deploy.sh
```

**Option B: Manual Setup**
```bash
# Create S3 bucket
aws s3 mb s3://your-transcription-bucket --region us-east-1
```

### 4. Set Up IAM Permissions

Ensure your AWS credentials have access to:
- **Amazon S3**: `s3:PutObject`, `s3:GetObject`
- **Amazon Transcribe**: `transcribe:StartTranscriptionJob`, `transcribe:GetTranscriptionJob`, `transcribe:DeleteTranscriptionJob`
- **Amazon Bedrock**: `bedrock:InvokeModel`

### 5. Configure Environment Variables

The `deploy.sh` script automatically creates a `.env` file, or you can create one manually:

```bash
# Create .env file
cat > .env << EOF
AWS_REGION=us-east-1
S3_BUCKET=your-transcription-bucket
EOF
```

Or set environment variables directly:

```bash
export AWS_REGION=us-east-1
export S3_BUCKET=your-transcription-bucket
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
├── deploy.sh                 # Simplified AWS setup script (S3 bucket only)
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
