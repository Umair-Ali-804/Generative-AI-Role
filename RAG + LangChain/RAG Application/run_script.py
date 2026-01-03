#!/usr/bin/env python3
"""
Unified script to run both FastAPI and Streamlit servers
"""
import subprocess
import time
import sys
import os
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed."""
    try:
        import fastapi
        import streamlit
        import langchain
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists."""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("Creating .env from .env.example...")
        
        example_file = Path(".env.example")
        if example_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            print("✅ .env file created")
            print("⚠️  Please edit .env and add your GOOGLE_API_KEY")
            return False
        else:
            print("❌ .env.example not found")
            return False
    return True

def start_fastapi():
    """Start FastAPI server."""
    print("\n🚀 Starting FastAPI server...")
    cmd = [sys.executable, "main.py"]
    return subprocess.Popen(cmd)

def start_streamlit():
    """Start Streamlit server."""
    print("\n🚀 Starting Streamlit server...")
    cmd = [sys.executable, "-m", "streamlit", "run", "streamlit_app.py"]
    return subprocess.Popen(cmd)

def main():
    print("=" * 60)
    print("RAG Q&A System - Startup Script")
    print("=" * 60)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check .env file
    if not check_env_file():
        print("\n⚠️  Please configure your .env file and run again")
        sys.exit(1)
    
    try:
        # Start FastAPI
        fastapi_process = start_fastapi()
        
        # Wait for FastAPI to start
        print("\n⏳ Waiting for FastAPI to start (5 seconds)...")
        time.sleep(5)
        
        # Start Streamlit
        streamlit_process = start_streamlit()
        
        print("\n" + "=" * 60)
        print("✅ Both servers started successfully!")
        print("=" * 60)
        print("\n📍 URLs:")
        print("   - FastAPI: http://localhost:8000")
        print("   - API Docs: http://localhost:8000/docs")
        print("   - Streamlit: http://localhost:8501")
        print("\n⏹️  Press Ctrl+C to stop both servers")
        print("=" * 60 + "\n")
        
        # Wait for user interrupt
        try:
            fastapi_process.wait()
            streamlit_process.wait()
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping servers...")
            fastapi_process.terminate()
            streamlit_process.terminate()
            
            # Wait for processes to terminate
            fastapi_process.wait(timeout=5)
            streamlit_process.wait(timeout=5)
            
            print("✅ Servers stopped successfully")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()