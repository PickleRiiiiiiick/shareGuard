#!/usr/bin/env python3
"""Force restart ShareGuard backend"""

import subprocess
import time
import os
import sys
import urllib.request

def check_backend_status():
    """Check if backend is running"""
    try:
        with urllib.request.urlopen("http://localhost:8000/docs", timeout=5) as response:
            return response.status == 200
    except:
        return False

def kill_backend_processes():
    """Kill all backend-related processes"""
    try:
        # Kill by port
        subprocess.run(['fuser', '-k', '8000/tcp'], 
                      capture_output=True, stderr=subprocess.DEVNULL)
        time.sleep(2)
    except:
        pass
    
    try:
        # Kill uvicorn processes
        result = subprocess.run(['pkill', '-f', 'uvicorn'], 
                              capture_output=True)
        time.sleep(1)
    except:
        pass
    
    try:
        # Kill python app processes
        result = subprocess.run(['pkill', '-f', 'python.*app'], 
                              capture_output=True)
        time.sleep(1)
    except:
        pass

def start_backend():
    """Start the backend"""
    try:
        os.chdir('/mnt/c/ShareGuard')
        
        # Try to start with Python directly
        env = os.environ.copy()
        env['PYTHONPATH'] = '/mnt/c/ShareGuard'
        
        print("Starting backend with uvicorn...")
        
        # Start in background
        proc = subprocess.Popen([
            'python3', '-m', 'uvicorn', 'src.app:app',
            '--reload', '--host', '0.0.0.0', '--port', '8000'
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return proc
        
    except Exception as e:
        print(f"Error starting backend: {e}")
        return None

def main():
    print("ShareGuard Backend Force Restart")
    print("=" * 40)
    
    print("1. Checking current backend status...")
    if check_backend_status():
        print("   Backend is running")
    else:
        print("   Backend not responding properly")
    
    print("2. Killing backend processes...")
    kill_backend_processes()
    
    print("3. Waiting 5 seconds...")
    time.sleep(5)
    
    print("4. Starting new backend...")
    proc = start_backend()
    
    if proc:
        print("5. Waiting for backend to start...")
        
        # Wait up to 30 seconds for backend to start
        for i in range(30):
            time.sleep(1)
            if check_backend_status():
                print(f"✓ Backend started successfully after {i+1} seconds!")
                print("Backend should now have the WebSocket auth fix applied.")
                return
            print(f"   Waiting... ({i+1}/30)")
        
        print("✗ Backend did not start within 30 seconds")
        
        # Show some output
        try:
            stdout, stderr = proc.communicate(timeout=1)
            if stdout:
                print("STDOUT:", stdout.decode()[:500])
            if stderr:
                print("STDERR:", stderr.decode()[:500])
        except:
            pass
    else:
        print("✗ Failed to start backend process")

if __name__ == "__main__":
    main()