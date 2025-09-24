#!/usr/bin/env python3
"""Quick start script for the Meeting Transcription & AI Analysis App"""

import subprocess
import sys
import os

def main():
    print("🎙️ Meeting Transcription & AI Analysis App")
    print("=" * 50)
    
    # Install uv if needed
    try:
        subprocess.check_call(["uv", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("📦 Installing uv...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uv"])
    
    # Install dependencies
    try:
        import gradio, boto3
    except ImportError:
        print("📦 Installing dependencies...")
        subprocess.check_call(["uv", "sync"])
    
    # Check AWS config
    try:
        import boto3
        boto3.client('sts').get_caller_identity()
        print("✅ AWS configured")
    except:
        print("⚠️  AWS not configured - set credentials or run ./deploy.sh")
    
    print("\n🚀 Starting app at http://localhost:7860")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        subprocess.check_call(["uv", "run", "python", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Stopped")

if __name__ == "__main__":
    main()
