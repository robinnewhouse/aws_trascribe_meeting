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

def upload_to_s3(audio_file, filename):
    """Upload audio file to S3 and return the S3 key"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    s3_key = f"audio-uploads/{timestamp}_{filename}"
    s3.upload_file(audio_file, S3_BUCKET, s3_key)
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
        
        yield "Complete!", clean_transcript, ai_analysis
        
    except Exception as e:
        yield f"Error: {str(e)}", "", ""

# Create Gradio interface
with gr.Blocks(title="Meeting Transcription & Analysis") as app:
    gr.Markdown("# 🎙️ Meeting Transcription & AI Analysis")
    
    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(label="Upload Audio", type="filepath")
            instructions_input = gr.Textbox(
                label="Analysis Instructions",
                placeholder="Focus on action items and decisions made",
                lines=3,
                value="Provide a comprehensive summary focusing on key decisions, action items, and important insights."
            )
            submit_btn = gr.Button("🚀 Process Recording", variant="primary")
        
        with gr.Column(scale=2):
            status_output = gr.Textbox(label="Status", interactive=False, lines=2)
            
            with gr.Row():
                transcript_output = gr.Textbox(label="📝 Transcript", lines=15, interactive=False)
                analysis_output = gr.Textbox(label="🧠 AI Analysis", lines=15, interactive=False)
    
    submit_btn.click(
        fn=process_audio,
        inputs=[audio_input, instructions_input],
        outputs=[status_output, transcript_output, analysis_output]
    )
    
    gr.Markdown("""
    ## Setup
    1. AWS credentials configured
    2. Environment variables: AWS_REGION, S3_BUCKET
    3. Bedrock access enabled for OpenAI GPT models
    """)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
