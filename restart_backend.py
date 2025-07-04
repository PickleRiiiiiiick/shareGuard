#!/usr/bin/env python3
"""Restart the ShareGuard backend"""

import subprocess
import time
import sys
import os
import signal

def find_and_kill_backend():
    """Find and kill running backend processes"""
    try:
        # Try to find uvicorn processes
        result = subprocess.run(['pgrep', '-f', 'uvicorn.*app'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid.strip():
                    print(f"Killing backend process {pid}")
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(1)
                    # Force kill if still running
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
        
        # Also try to kill any Python processes running app.py
        result = subprocess.run(['pgrep', '-f', 'python.*app'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid.strip():
                    print(f"Killing Python app process {pid}")
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        time.sleep(1)
                        os.kill(int(pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                        
    except Exception as e:
        print(f"Error killing processes: {e}")

def start_backend():
    """Start the backend using the activation script"""
    try:
        # Change to ShareGuard directory
        os.chdir('/mnt/c/ShareGuard')
        
        # Check if virtual environment exists
        venv_activate = './venv/Scripts/activate'
        if not os.path.exists(venv_activate):
            venv_activate = './venv/bin/activate'
        
        if not os.path.exists(venv_activate):
            print("Virtual environment not found. Starting without venv...")
            # Try to start directly
            subprocess.Popen(['python3', '-m', 'uvicorn', 'src.app:app', 
                            '--reload', '--host', '0.0.0.0', '--port', '8000'])
        else:
            # Use the PowerShell start script
            print("Starting backend with start-backend.ps1...")
            subprocess.Popen(['powershell', '-File', './start-backend.ps1'])
            
    except Exception as e:
        print(f"Error starting backend: {e}")

def main():
    print("ShareGuard Backend Restart")
    print("=" * 30)
    
    print("1. Stopping existing backend...")
    find_and_kill_backend()
    
    print("2. Waiting 3 seconds...")
    time.sleep(3)
    
    print("3. Starting backend...")
    start_backend()
    
    print("4. Backend restart initiated!")
    print("Please wait 10-15 seconds for the backend to fully start.")

if __name__ == "__main__":
    main()