#!/usr/bin/env python3
"""Test WebSocket with a valid token"""

import socket
import base64
import urllib.parse
import urllib.request
import json

def get_valid_token():
    """Get a valid authentication token"""
    try:
        login_data = {
            "username": "ShareGuardService",
            "domain": "shareguard.com",
            "password": "ShareGuardService"
        }
        
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/auth/login",
            data=json.dumps(login_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get('access_token')
    except Exception as e:
        print(f"Failed to get token: {e}")
        return None

def test_websocket_with_valid_token():
    """Test WebSocket with a valid authentication token"""
    print("Testing WebSocket with valid token...")
    
    # Get a valid token
    token = get_valid_token()
    if not token:
        print("✗ Could not get valid token")
        return
    
    print(f"✓ Got valid token: {token[:50]}...")
    
    host = "localhost"
    port = 8000
    
    ws_key = base64.b64encode(b'1234567890123456').decode('utf-8')
    params = urllib.parse.urlencode({
        "token": token,
        "filters": "{}"
    })
    
    handshake = f"""GET /api/v1/alerts/notifications?{params} HTTP/1.1\r
Host: {host}:{port}\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Key: {ws_key}\r
Sec-WebSocket-Version: 13\r
Origin: http://localhost:5174\r
\r
"""
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        print("Sending WebSocket handshake with valid token...")
        sock.send(handshake.encode())
        
        response = sock.recv(4096).decode('utf-8', errors='ignore')
        
        print("Response:")
        print("-" * 50)
        print(response)
        print("-" * 50)
        
        if "101 Switching Protocols" in response:
            print("🎉 WebSocket handshake SUCCESSFUL!")
            print("✅ WebSocket authentication fix is working!")
            
            # Try to read initial message
            try:
                sock.settimeout(5)
                initial_data = sock.recv(1024)
                if initial_data:
                    print(f"✓ Received initial WebSocket data: {len(initial_data)} bytes")
                    
                    # Try to parse WebSocket frame
                    if len(initial_data) >= 2:
                        opcode = initial_data[0] & 0x0F
                        payload_len = initial_data[1] & 0x7F
                        
                        if opcode == 1 and payload_len < 126:  # Text frame
                            payload = initial_data[2:2+payload_len]
                            try:
                                text = payload.decode('utf-8')
                                print(f"✓ WebSocket message: '{text}'")
                            except:
                                print(f"✓ WebSocket binary data: {payload}")
                                
            except socket.timeout:
                print("⚠ No initial message received (normal)")
                
        elif "403" in response:
            print("✗ Still getting 403 - WebSocket handler may have auth issues")
        elif "401" in response:
            print("✗ Token authentication failed")
        elif "400" in response:
            print("✗ Bad request - WebSocket headers may be malformed")
        else:
            print("? Unexpected response")
            
        sock.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    print("ShareGuard WebSocket Valid Token Test")
    print("=" * 50)
    
    test_websocket_with_valid_token()
    
    print("\n" + "=" * 50)
    print("Test completed!")