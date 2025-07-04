#!/usr/bin/env python3
"""Test WebSocket endpoint bypassing authentication temporarily"""

import socket
import base64
import json
import urllib.parse

def test_websocket_without_auth():
    """Test WebSocket handshake without authentication to see if endpoint exists"""
    print("Testing WebSocket endpoint without authentication...")
    
    host = "localhost"
    port = 8000
    
    # Create WebSocket key
    ws_key = base64.b64encode(b'1234567890123456').decode('utf-8')
    
    # Build handshake request without auth
    handshake = f"""GET /api/v1/alerts/notifications HTTP/1.1\r
Host: {host}:{port}\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Key: {ws_key}\r
Sec-WebSocket-Version: 13\r
Origin: http://localhost:5173\r
\r
"""
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        print("✓ TCP connection established")
        print(f"Sending handshake to /api/v1/alerts/notifications...")
        
        sock.send(handshake.encode())
        
        response = sock.recv(4096).decode('utf-8', errors='ignore')
        print(f"\nResponse:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        
        if "101 Switching Protocols" in response:
            print("\n✓ WebSocket upgrade successful (no auth required!)")
        elif "401" in response:
            print("\n✓ Authentication required (expected)")
        elif "404" in response:
            print("\n✗ Endpoint not found")
        elif "426" in response:
            print("\n✓ Upgrade required (endpoint exists)")
        else:
            print(f"\n? Unexpected response")
        
        sock.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")

def test_websocket_with_dummy_token():
    """Test WebSocket with a dummy token to see auth behavior"""
    print("\n\nTesting WebSocket with dummy token...")
    
    host = "localhost"
    port = 8000
    dummy_token = "dummy.token.here"
    
    ws_key = base64.b64encode(b'1234567890123456').decode('utf-8')
    params = urllib.parse.urlencode({
        "token": dummy_token,
        "filters": "{}"
    })
    
    handshake = f"""GET /api/v1/alerts/notifications?{params} HTTP/1.1\r
Host: {host}:{port}\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Key: {ws_key}\r
Sec-WebSocket-Version: 13\r
Origin: http://localhost:5173\r
\r
"""
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        sock.send(handshake.encode())
        response = sock.recv(4096).decode('utf-8', errors='ignore')
        
        print(f"Response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        
        if "101 Switching Protocols" in response:
            print("\n⚠ WebSocket upgrade successful with dummy token!")
        elif "401" in response or "1008" in response:
            print("\n✓ Authentication properly rejected")
        elif "404" in response:
            print("\n✗ Endpoint not found")
        else:
            print(f"\n? Unexpected response")
            
        sock.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")

def test_websocket_malformed_request():
    """Test WebSocket with malformed request"""
    print("\n\nTesting WebSocket with malformed request...")
    
    host = "localhost"
    port = 8000
    
    # Invalid handshake
    handshake = f"""GET /api/v1/alerts/notifications HTTP/1.1\r
Host: {host}:{port}\r
\r
"""
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        sock.send(handshake.encode())
        response = sock.recv(4096).decode('utf-8', errors='ignore')
        
        print(f"Response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        
        sock.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    print("ShareGuard WebSocket Endpoint Test")
    print("=" * 50)
    
    test_websocket_without_auth()
    test_websocket_with_dummy_token()
    test_websocket_malformed_request()
    
    print("\n" + "=" * 50)
    print("Test completed!")