#!/usr/bin/env python3
"""Simple WebSocket test using standard libraries"""

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

def test_websocket_handshake():
    """Test WebSocket handshake manually"""
    
    # Configuration
    host = "localhost"
    port = 8000
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InNoYXJlZ3VhcmQuY29tXFxTaGFyZUd1YXJkU2VydmljZSIsImV4cCI6MTc1MTY2NjQwMSwiaWF0IjoxNzUxNTgwMDAxfQ.rkiw2vL9jxiFhIedmBpvyQxsKHE2JcjdvHvgYf5ehvo"
    
    print("Testing WebSocket handshake...")
    print(f"Target: ws://{host}:{port}/api/v1/alerts/notifications")
    print("-" * 50)
    
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        print(f"\n1. Connecting to {host}:{port}...")
        sock.connect((host, port))
        print("✓ TCP connection established")
        
        # Prepare WebSocket handshake
        ws_key = create_websocket_key()
        params = urlencode({"filters": "{}", "token": token})
        
        handshake = f"""GET /api/v1/alerts/notifications?{params} HTTP/1.1\r
Host: {host}:{port}\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Key: {ws_key}\r
Sec-WebSocket-Version: 13\r
Origin: http://localhost:5173\r
\r
"""
        
        print("\n2. Sending WebSocket handshake...")
        print("Request headers:")
        print(handshake.replace('\r\n', '\n'))
        
        sock.send(handshake.encode())
        
        # Receive response
        print("3. Waiting for response...")
        response = sock.recv(4096).decode('utf-8', errors='ignore')
        
        print("Response:")
        print(response)
        
        # Check if upgrade was successful
        if "101 Switching Protocols" in response:
            print("\n✓ WebSocket handshake successful!")
        else:
            print("\n✗ WebSocket handshake failed")
            
        sock.close()
        
    except socket.timeout:
        print("✗ Connection timed out")
    except ConnectionRefusedError:
        print("✗ Connection refused - is the backend running?")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")

def test_http_connection():
    """Test basic HTTP connection to backend"""
    
    print("\n\nTesting HTTP connection...")
    print("-" * 50)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        print("Connecting to localhost:8000...")
        sock.connect(("localhost", 8000))
        
        # Send HTTP request
        request = """GET /docs HTTP/1.1\r
Host: localhost:8000\r
\r
"""
        sock.send(request.encode())
        
        # Get response
        response = sock.recv(1024).decode('utf-8', errors='ignore')
        status_line = response.split('\n')[0]
        print(f"Response: {status_line}")
        
        sock.close()
        
        if "200 OK" in status_line:
            print("✓ Backend is running and accessible")
        else:
            print("✗ Backend returned unexpected status")
            
    except ConnectionRefusedError:
        print("✗ Cannot connect to backend on localhost:8000")
        print("  Make sure the backend is running with: .\\start-backend.ps1")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    print("ShareGuard WebSocket Connection Test (Simple)")
    print("=" * 50)
    
    # First test if backend is running
    test_http_connection()
    
    # Then test WebSocket
    test_websocket_handshake()
    
    print("\n" + "=" * 50)
    print("Test completed!")