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
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('S3_BUCKET', 'your-transcription-bucket')

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
    temp_file.write(content)
    temp_file.close()
    return temp_file.name

def process_audio(audio_file, instructions):
    """Main function to process audio file through the entire pipeline"""
    if audio_file is None:
        return "Please upload an audio file.", "", ""
    
    try:
        yield "Uploading audio to S3...", "", ""
        filename = os.path.basename(audio_file)
        s3_key = upload_to_s3(audio_file, filename)
        
        yield "Starting transcription...", "", ""
        job_name = start_transcription(s3_key, filename)
        
        yield f"Transcribing...", "", ""
        raw_transcript = wait_for_transcription(job_name)
        
        yield "Processing transcript...", "", ""
        clean_transcript = parse_transcript(raw_transcript)
        
        yield "Generating AI analysis...", clean_transcript, ""
        ai_analysis = get_bedrock_analysis(clean_transcript, instructions)
        
        yield "Uploading to S3...", clean_transcript, ai_analysis
        upload_text_to_s3(clean_transcript, filename, "processed")
        upload_text_to_s3(ai_analysis, filename, "summary")
        
        yield "Complete! All files saved to S3.", clean_transcript, ai_analysis
        
    except Exception as e:
        yield f"Error: {str(e)}", "", ""

# Create Gradio interface
with gr.Blocks(title="Meeting Transcription & Analysis", theme=app_theme) as demo:
    gr.Markdown("## 🎙️ Meeting Transcription & AI Analysis")
    gr.Markdown("Capture conversations, then review the transcript and AI summary without leaving this page.")

    with gr.Column():
        audio_input = gr.Audio(label="Upload Audio", type="filepath")

        instructions_input = gr.Textbox(
            label="Analysis Instructions",
            placeholder="Highlight decisions, action items, and owners",
            lines=3,
            value="Provide a comprehensive summary focusing on key decisions, action items, and important insights."
        )

        submit_btn = gr.Button("🚀 Process Recording", variant="primary")

        gr.Markdown("## Status")
        status_output = gr.Markdown("")

        gr.Markdown("## 📝 Transcript")
        transcript_output = gr.Textbox(label="📝 Transcript", lines=16, interactive=False, show_label=False)
        with gr.Row():
            transcript_download = gr.DownloadButton(label="📥 Download Transcript", variant="secondary")
            transcript_copy = gr.Button("📋 Copy to Clipboard", variant="secondary")

        gr.Markdown("## 🧠 AI Analysis")
        analysis_output = gr.Textbox(label="🧠 AI Analysis", lines=16, interactive=False, show_label=False)
        with gr.Row():
            analysis_download = gr.DownloadButton(label="📥 Download Analysis", variant="secondary")
            analysis_copy = gr.Button("📋 Copy to Clipboard", variant="secondary")

    submit_btn.click(
        fn=process_audio,
        inputs=[audio_input, instructions_input],
        outputs=[status_output, transcript_output, analysis_output]
    )
    
    # Download button handlers
    transcript_download.click(
        fn=lambda x: create_download_file(x, "transcript") if x else None,
        inputs=[transcript_output],
        outputs=[transcript_download]
    )
    
    analysis_download.click(
        fn=lambda x: create_download_file(x, "analysis") if x else None,
        inputs=[analysis_output],
        outputs=[analysis_download]
    )
    
    # Copy button handlers (these will use browser clipboard API)
    transcript_copy.click(
        fn=None,
        js="(text) => navigator.clipboard.writeText(text)",
        inputs=[transcript_output]
    )
    
    analysis_copy.click(
        fn=None,
        js="(text) => navigator.clipboard.writeText(text)",
        inputs=[analysis_output]
    )
    
    gr.Markdown("""
    ## Setup
    1. AWS credentials configured
    2. Environment variables: AWS_REGION, S3_BUCKET
    3. Bedrock access enabled for OpenAI GPT models
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
