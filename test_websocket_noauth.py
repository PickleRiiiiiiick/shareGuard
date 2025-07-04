#!/usr/bin/env python3
"""Test WebSocket connection without authentication to see raw response"""

import socket
import base64
import hashlib
import sys
import json
from urllib.parse import urlencode, urlparse

def create_websocket_key():
    """Generate a WebSocket key"""
    key = base64.b64encode(b'1234567890123456').decode('utf-8')
    return key

def test_websocket_raw():
    """Test WebSocket connection without any authentication"""
    
    # Configuration
    host = "localhost"
    port = 8000
    
    print("Testing WebSocket without authentication...")
    print(f"Target: ws://{host}:{port}/api/v1/alerts/notifications")
    print("-" * 50)
    
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        print(f"\n1. Connecting to {host}:{port}...")
        sock.connect((host, port))
        print("✓ TCP connection established")
        
        # Prepare WebSocket handshake WITHOUT token
        ws_key = create_websocket_key()
        params = urlencode({"filters": "{}"})  # No token parameter
        
        handshake = f"""GET /api/v1/alerts/notifications?{params} HTTP/1.1\r
Host: {host}:{port}\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Key: {ws_key}\r
Sec-WebSocket-Version: 13\r
Origin: http://localhost:5173\r
\r
"""
        
        print("\n2. Sending WebSocket handshake (no auth)...")
        print("Request headers:")
        print(handshake.replace('\r\n', '\n'))
        
        sock.send(handshake.encode())
        
        # Receive response
        print("3. Waiting for response...")
        response = sock.recv(4096).decode('utf-8', errors='ignore')
        
        print("Response:")
        print(response)
        
        # Parse response headers
        lines = response.split('\r\n')
        status_line = lines[0] if lines else ""
        
        if "101 Switching Protocols" in status_line:
            print("\n✓ WebSocket handshake successful (no auth required?)")
        elif "1008" in response:
            print("\n✗ WebSocket closed with code 1008 (Policy Violation - auth required)")
        else:
            print(f"\n✗ Unexpected response: {status_line}")
            
        sock.close()
        
    except socket.timeout:
        print("✗ Connection timed out")
    except ConnectionRefusedError:
        print("✗ Connection refused - is the backend running?")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    print("ShareGuard WebSocket Raw Connection Test")
    print("=" * 50)
    
    test_websocket_raw()
    
    print("\n" + "=" * 50)
    print("Test completed!")