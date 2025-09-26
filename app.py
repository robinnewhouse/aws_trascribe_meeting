import gradio as gr
import boto3
import json
import time
import os
import uuid
from dotenv import load_dotenv
from datetime import datetime
from parse_transcribe_output import function as parse_transcript

load_dotenv(override=True)

# For Hugging Face Spaces, check for HF secrets first, then fall back to .env
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('S3_BUCKET', 'your-transcription-bucket')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Configure AWS credentials if provided
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    import boto3
    boto3.setup_default_session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

# AWS clients
s3 = boto3.client('s3', region_name=AWS_REGION)
transcribe = boto3.client('transcribe', region_name=AWS_REGION)
bedrock = boto3.client('bedrock-runtime', region_name=AWS_REGION)

# File format mapping
FORMATS = {'wav': 'wav', 'mp3': 'mp3', 'mp4': 'mp4', 'm4a': 'mp4', 'flac': 'flac', 'ogg': 'ogg', 'amr': 'amr', 'webm': 'webm'}

app_theme = gr.themes.Soft(
    primary_hue="indigo",
    neutral_hue="gray",
    spacing_size="lg",
    font=["Inter", "sans-serif"]
)

def upload_to_s3(audio_file, filename):
    """Upload audio file to S3 and return the S3 key"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    s3_key = f"audio-uploads/{timestamp}_{filename}"
    s3.upload_file(audio_file, S3_BUCKET, s3_key)
    return s3_key

def upload_text_to_s3(content, base_filename, suffix):
    """Upload text content to S3 with specified suffix"""
    name_without_ext = os.path.splitext(base_filename)[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    s3_key = f"processed-outputs/{timestamp}_{name_without_ext}_{suffix}.txt"
    
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=content)
    return s3_key

def start_transcription(s3_key, filename):
    """Start transcription job and return job name"""
    job_name = f"transcription-job-{uuid.uuid4().hex[:8]}-{int(time.time())}"
    media_format = FORMATS.get(filename.split('.')[-1].lower(), 'wav')
    
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': f"s3://{S3_BUCKET}/{s3_key}"},
        MediaFormat=media_format,
        LanguageCode='en-US',
        Settings={"ShowSpeakerLabels": True, "MaxSpeakerLabels": 10},
        OutputBucketName=S3_BUCKET,
        OutputKey=f"transcriptions/{job_name}.json"
    )
    return job_name

def wait_for_transcription(job_name):
    """Poll transcription job until completion and return transcript"""
    for _ in range(60):  # 10 minutes max
        response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        status = response['TranscriptionJob']['TranscriptionJobStatus']
        
        if status == 'COMPLETED':
            transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
            transcript_key = transcript_uri.split(f"{S3_BUCKET}/")[1]
            
            # Download transcript from S3
            transcript_response = s3.get_object(Bucket=S3_BUCKET, Key=transcript_key)
            transcript_content = transcript_response['Body'].read().decode('utf-8')
            transcript_json = json.loads(transcript_content)
            
            # Clean up
            try:
                transcribe.delete_transcription_job(TranscriptionJobName=job_name)
            except:
                pass
            
            return str(transcript_json)
            
        elif status == 'FAILED':
            reason = response['TranscriptionJob'].get('FailureReason', 'Unknown error')
            raise Exception(f'Transcription failed: {reason}')
        
        time.sleep(10)
    
    raise Exception('Transcription timed out')

def get_bedrock_analysis(transcript, instructions):
    """Use Bedrock to analyze the transcript and generate insights"""
    prompt = f"""Instructions: {instructions}

Meeting Transcript:
{transcript}

Provide a comprehensive summary including:
1. Key discussion points
2. Decisions made
3. Action items
4. Important insights
5. Next steps

Format with clear sections and headers."""
    
    # Use correct OpenAI format (not Anthropic format)
    body = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
        "temperature": 0.7
    }
        
    try:
        response = bedrock.invoke_model(
            modelId="openai.gpt-oss-120b-1:0",
            body=json.dumps(body)
        )
        content = json.loads(response['body'].read())['choices'][0]['message']['content']
        
        # Remove reasoning tags if present
        if '<reasoning>' in content:
            content = content.split('</reasoning>')[-1].strip()
        
        return content
    except Exception as e:
        print(f"DEBUG: Error type: {type(e).__name__}")
        print(f"DEBUG: Error message: {str(e)}")
        raise

def create_download_file(content, filename):
    """Create a temporary file for download"""
    import tempfile
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', prefix=filename+'_')
    temp_file.write(content or "")
    temp_file.close()
    return temp_file.name

def format_status(message, status="processing"):
    """Format status messages with simple styling"""
    if status == "error":
        return f"❌ {message}"
    elif status == "complete":
        return f"✅ {message}"
    else:
        return f"🔄 {message}"

def process_audio(audio_file, instructions):
    """Main function to process audio file through the entire pipeline"""
    print(f"DEBUG: process_audio called with audio_file={audio_file}, instructions={instructions}")
    
    if audio_file is None:
        yield f"<span class='chip chip--error'>Please upload an audio file first</span>", "", "", ""
        return

    try:
        yield f"<span class='chip chip--processing'>Uploading audio file to S3...</span>", "Uploading audio file to S3...", "", ""
        filename = os.path.basename(audio_file)
        
        # Check if AWS credentials are configured
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            raise Exception("AWS credentials not configured. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
        
        s3_key = upload_to_s3(audio_file, filename)

        yield f"<span class='chip chip--processing'>Starting AWS Transcribe job...</span>", "Starting AWS Transcribe job...", "", ""
        job_name = start_transcription(s3_key, filename)

        yield f"<span class='chip chip--processing'>Transcribing audio (this may take a few minutes)...</span>", "Transcribing audio (this may take a few minutes)...", "", ""
        raw_transcript = wait_for_transcription(job_name)

        yield f"<span class='chip chip--processing'>Processing and cleaning transcript...</span>", "Processing and cleaning transcript...", "", ""
        
        # Get clean text for analysis and display
        clean_transcript = parse_transcript(raw_transcript)

        yield f"<span class='chip chip--processing'>Generating AI-powered analysis...</span>", "Generating AI-powered analysis...", clean_transcript, ""
        ai_analysis = get_bedrock_analysis(clean_transcript, instructions)

        yield f"<span class='chip chip--processing'>Saving results to S3...</span>", "Saving results to S3...", clean_transcript, ai_analysis
        upload_text_to_s3(clean_transcript, filename, "processed")
        upload_text_to_s3(ai_analysis, filename, "summary")

        yield f"<span class='chip chip--success'>Ready. Last run: {datetime.now().strftime('%H:%M:%S')}.</span>", "Processing complete! Results ready for download.", clean_transcript, ai_analysis

    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        yield f"<span class='chip chip--error'>{error_msg}</span>", f"Error: {str(e)}", "", ""
        return

def safe_process_audio(audio_file, prompt):
    """Safe wrapper for process_audio with error handling"""
    print(f"DEBUG: safe_process_audio called with audio_file={audio_file}, prompt={prompt}")
    
    # First yield to show we're starting
    yield f"<span class='chip chip--processing'>Starting processing...</span>", "Starting processing...", "", ""
    
    try:
        for result in process_audio(audio_file, prompt):
            yield result
    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        print(f"DEBUG: Exception in safe_process_audio: {e}")
        yield f"<span class='chip chip--error'>{error_msg}</span>", f"Error: {str(e)}", "", ""

# Default analysis prompt
DEFAULT_PROMPT = "Analyze this meeting and provide key decisions, action items, and insights."

# Session state for persistence
session_state = gr.State({"prompt": DEFAULT_PROMPT})

# Create Gradio interface
with gr.Blocks(title="Meeting Transcription & Analysis", theme=app_theme) as demo:


    # Compact header
    with gr.Row(equal_height=True):
        gr.Markdown("### Meeting Transcription · AI Analysis")
        with gr.Row(scale=0):
            gr.Button("GitHub", link="https://github.com/robinnewhouse/aws_trascribe_meeting", size="sm")

    # Empty state hint
    empty_state = gr.Markdown("> 📎 Upload audio or record to begin.", visible=False)

    # Audio upload with validation
    with gr.Column():
        audio = gr.Audio(
            sources=["upload", "microphone"],
            type="filepath",
            label="Audio",
            elem_id="audio_input"
        )
        gr.Markdown("**Supported**: mp3, wav, m4a · **Limit**: 120 min / 200 MB")

    # Analysis prompt in collapsible accordion
    with gr.Accordion("Analysis Prompt", open=False):
        prompt = gr.Textbox(
            lines=4,
            value=DEFAULT_PROMPT,
            placeholder="Enter analysis instructions...",
            label="Analysis Instructions",
            elem_id="analysis_prompt"
        )

    # Primary CTA button
    run = gr.Button(
        "⚡ Process",
        variant="primary",
        interactive=False,
        elem_id="process_button"
    )

    # Status and logs
    status = gr.HTML("<span class='chip chip--ready'>Ready</span>")
    logs = gr.Code(
        label="Logs",
        visible=False,
        elem_id="logs_output"
    )

    # Transcript output
    gr.Markdown("### Transcript")
    transcript = gr.Textbox(
        label="Raw Transcript",
        lines=16,
        interactive=False,
        show_label=False,
        elem_id="transcript_output"
    )
    with gr.Row():
        transcript_copy = gr.Button("Copy", variant="secondary", elem_id="copy_transcript")
        transcript_download = gr.DownloadButton("Download .txt", variant="secondary", elem_id="download_transcript")

    # Analysis output
    gr.Markdown("### Structured Summary")
    analysis = gr.Textbox(
        label="AI Analysis",
        lines=12,
        interactive=False,
        show_label=False,
        elem_id="analysis_output"
    )
    with gr.Row():
        analysis_copy = gr.Button("Copy", variant="secondary", elem_id="copy_analysis")
        analysis_download = gr.DownloadButton("Download .txt", variant="secondary", elem_id="download_analysis")

    # Technical overview section
    with gr.Accordion("🔧 How It Works - Technical Overview", open=False):
        gr.Markdown("""
        ### Architecture
        
        This application follows a straightforward pipeline architecture that processes audio files through AWS services:
        
        **Frontend (Gradio)** → **S3 Storage** → **AWS Transcribe** → **Transcript Parser** → **AWS Bedrock** → **Results Display**
        
        ### Processing Pipeline
        
        1. **Audio Upload & Storage**
           - User uploads audio file through Gradio interface
           - File is uploaded to designated S3 bucket with timestamped key (`audio-uploads/{timestamp}_{filename}`)
           - Supports multiple formats: WAV, MP3, MP4/M4A, FLAC, OGG, AMR, WebM
        
        2. **Transcription Job**
           - AWS Transcribe job is initiated with speaker identification enabled (`ShowSpeakerLabels: True`)
           - Transcription output is automatically saved to S3 (`transcriptions/{job_name}.json`)
           - Job polling mechanism checks status every 10 seconds with 10-minute timeout
           - Completed jobs are automatically cleaned up to avoid resource accumulation
        
        3. **Transcript Processing**
           - Raw JSON output from Transcribe contains word-level timestamps and speaker labels
           - Custom parser (`parse_transcribe_output.py`) extracts speaker segments using regex pattern matching
           - Groups consecutive words by speaker, handling punctuation attachment
           - Outputs clean conversation format: `spk_0: Hello everyone...`
        
        4. **AI Analysis**
           - Clean transcript is sent to AWS Bedrock (OpenAI GPT model)
           - Configurable analysis prompt allows custom instruction injection
           - Response formatted into structured sections: key points, decisions, action items, insights, next steps
           - Uses OpenAI message format with temperature 0.7 for balanced creativity/consistency
        
        5. **Results Storage & Display**
           - Both transcript and analysis are uploaded to S3 for persistence (`processed-outputs/`)
           - Results displayed in Gradio interface with copy/download functionality
           - Temporary files created for download feature with automatic cleanup
        
        ### Key Technical Decisions
        
        - **Direct AWS Integration**: Eliminates Lambda overhead by calling AWS services directly from Gradio app
        - **Polling vs Webhooks**: Simple polling approach avoids complex webhook infrastructure setup
        - **Speaker Grouping**: Custom parser groups consecutive speaker segments for natural conversation flow
        - **Stateless Design**: Each processing request is independent with no session persistence required
        - **Error Handling**: Comprehensive try/catch blocks with user-friendly error messages
        
        ### Security & Permissions
        
        The application requires minimal AWS permissions:
        - S3: `GetObject`, `PutObject` for file storage
        - Transcribe: `StartTranscriptionJob`, `GetTranscriptionJob`, `DeleteTranscriptionJob`
        - Bedrock: `InvokeModel` for AI analysis
        
        Uses IAM policies with resource-specific restrictions to follow least-privilege principle.
        """)

    # Event handlers
    def update_ui_on_audio_change(audio_file):
        """Enable/disable run button based on audio presence"""
        if audio_file:
            return gr.update(value="<span class='chip chip--ready'>Ready</span>"), gr.update(visible=False), gr.update(interactive=True, variant="primary")
        else:
            return gr.update(value="<span class='chip chip--ready'>Ready</span>"), gr.update(visible=True), gr.update(interactive=False, variant="secondary")

    audio.change(
        fn=update_ui_on_audio_change,
        inputs=[audio],
        outputs=[status, empty_state, run]
    )

    run.click(
        fn=safe_process_audio,
        inputs=[audio, prompt],
        outputs=[status, logs, transcript, analysis],
        show_progress=True,
        api_name="process"
    )

    # Copy and download handlers
    transcript_copy.click(
        fn=None,
        js="(text) => navigator.clipboard.writeText(text)",
        inputs=[transcript]
    )

    transcript_download.click(
        fn=lambda x: create_download_file(x, "transcript") if x else None,
        inputs=[transcript],
        outputs=[transcript_download]
    )

    analysis_copy.click(
        fn=None,
        js="(text) => navigator.clipboard.writeText(text)",
        inputs=[analysis]
    )

    analysis_download.click(
        fn=lambda x: create_download_file(x, "analysis") if x else None,
        inputs=[analysis],
        outputs=[analysis_download]
    )

    # Add keyboard navigation JavaScript
    gr.Markdown("""
    <script>
    // Focus process button when audio is uploaded
    document.addEventListener('DOMContentLoaded', function() {
        const audioInput = document.getElementById('audio_input');
        const processButton = document.getElementById('process_button');

        if (audioInput) {
            audioInput.addEventListener('change', function() {
                if (this.files && this.files.length > 0) {
                    setTimeout(() => processButton?.focus(), 100);
                }
            });
        }

        // ESC key to collapse accordions
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const accordions = document.querySelectorAll('details[open]');
                accordions.forEach(acc => acc.removeAttribute('open'));
            }
        });
    });
    </script>
    """)

if __name__ == "__main__":
    # Enable queue for processing (no concurrency_count parameter needed)
    demo.queue()

    # Add global CSS for centered layout and styling
    gr.Markdown("""
    <style>
    .gradio-container{max-width:1100px;margin:auto;padding:20px}
    :root { --radius-lg: 14px }
    .chip{padding:4px 8px;border-radius:999px;font-size:12px;font-weight:500;display:inline-block}
    .chip--success{background:#d1fae5;color:#065f46;border:1px solid #a7f3d0}
    .chip--error{background:#fee2e2;color:#991b1b;border:1px solid #fca5a5}
    .chip--processing{background:#fef3c7;color:#92400e;border:1px solid #fde68a}
    .chip--ready{background:#f0f9ff;color:#0c4a6e;border:1px solid #bae6fd}

    /* Improve spacing and typography */
    .gradio-container h3 { margin-top: 24px; margin-bottom: 12px; }
    .gradio-container .block { margin-bottom: 16px; }

    /* Better button spacing */
    .gradio-container .gr-button { margin: 2px 4px; }

    /* Improve accordion styling */
    .gradio-container details { margin: 16px 0; }
    .gradio-container details summary { cursor: pointer; padding: 8px 0; }

    /* Dataframe styling */
    .gradio-container table { font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace; }

    /* Button states */
    .gradio-container button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .gradio-container button:not(:disabled) {
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .gradio-container button:not(:disabled):hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    </style>
    """)

    demo.launch(server_name="0.0.0.0", server_port=7860)
