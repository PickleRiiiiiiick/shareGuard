#!/usr/bin/env python3
"""Simple WebSocket authentication test using urllib"""

import json
import urllib.request
import urllib.parse
import base64
import hashlib
import socket
import ssl

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/v1/alerts/notifications"

def get_auth_token():
    """Get authentication token from login endpoint"""
    print("[1] Getting authentication token...")
    
    login_data = json.dumps({
        "username": "ShareGuardService",
        "domain": "shareguard.com",
        "password": "ShareGuardService"
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/auth/login",
        data=login_data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            token = data['access_token']
            print(f"✓ Got token: {token[:50]}...")
            return token
    except Exception as e:
        print(f"✗ Failed to get token: {e}")
        return None

def test_websocket_handshake(token):
    """Test WebSocket handshake with authentication"""
    print("\n[2] Testing WebSocket handshake...")
    
    # Parse URL
    host = "localhost"
    port = 8000
    
    # Create WebSocket key
    ws_key = base64.b64encode(b'1234567890123456').decode('utf-8')
    
    # Build query string with token
    params = urllib.parse.urlencode({
        "token": token,
        "filters": "{}"
    })
    
    # Build handshake request
    handshake = f"""GET /api/v1/alerts/notifications?{params} HTTP/1.1\r
Host: {host}:{port}\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Key: {ws_key}\r
Sec-WebSocket-Version: 13\r
Origin: http://localhost:5173\r
\r
"""
    
    print(f"Connecting to {host}:{port}...")
    
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        print("✓ TCP connection established")
        
        # Send handshake
        print("\nSending handshake:")
        print("-" * 40)
        print(handshake.replace('\r\n', '\\r\\n\n'))
        print("-" * 40)
        
        sock.send(handshake.encode())
        
        # Receive response
        print("\nWaiting for response...")
        response = b""
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break
            response += chunk
            # Check if we have complete headers
            if b"\r\n\r\n" in response:
                break
        
        response_text = response.decode('utf-8', errors='ignore')
        print("\nResponse received:")
        print("-" * 40)
        print(response_text)
        print("-" * 40)
        
        # Check result
        if "101 Switching Protocols" in response_text:
            print("\n✓ WebSocket handshake successful!")
            
            # Try to read initial message
            print("\nWaiting for initial message...")
            sock.settimeout(5)
            try:
                # WebSocket frames are more complex, but let's try to read something
                initial_data = sock.recv(1024)
                if initial_data:
                    print(f"✓ Received data: {len(initial_data)} bytes")
                    # Try to parse if it looks like text
                    try:
                        # Skip WebSocket frame headers (simplified)
                        if len(initial_data) > 2:
                            payload_start = 2
                            if initial_data[1] & 0x7f == 126:
                                payload_start = 4
                            elif initial_data[1] & 0x7f == 127:
                                payload_start = 10
                            
                            text = initial_data[payload_start:].decode('utf-8', errors='ignore')
                            if text:
                                print(f"   Message content: {text}")
                    except:
                        pass
            except socket.timeout:
                print("⚠ No initial message received (timeout)")
                
        elif "401" in response_text or "403" in response_text:
            print("\n✗ Authentication failed")
        elif "400" in response_text:
            print("\n✗ Bad request")
        elif "426" in response_text:
            print("\n✗ Upgrade required")
        else:
            print("\n✗ Unexpected response")
        
        sock.close()
        
    except socket.timeout:
        print("✗ Connection timed out")
    except ConnectionRefusedError:
        print("✗ Connection refused - is the backend running?")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")

def test_websocket_endpoint_info(token):
    """Get information about WebSocket endpoint"""
    print("\n[3] Checking WebSocket endpoint info...")
    
    # Test if endpoint exists with regular GET
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/alerts/websocket-debug",
        headers={'Authorization': f'Bearer {token}'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("✓ WebSocket debug info:")
            print(f"   Stats: {data.get('websocket_stats')}")
            print(f"   Service running: {data.get('notification_service_running')}")
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP Error {e.code}: {e.reason}")
        if e.code == 404:
            print("   (Debug endpoint not found)")
    except Exception as e:
        print(f"✗ Error: {e}")

def check_backend_status():
    """Check if backend is running"""
    print("[0] Checking backend status...")
    
    try:
        req = urllib.request.Request(f"{BASE_URL}/docs")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                print("✓ Backend is running")
                return True
    except:
        print("✗ Backend is not accessible on localhost:8000")
        print("  Please run: .\\start-backend.ps1")
        return False
    
    return False

def main():
    print("ShareGuard WebSocket Authentication Test")
    print("=" * 50)
    
    # Check backend
    if not check_backend_status():
        return
    
    # Get token
    token = get_auth_token()
    if not token:
        return
    
    # Test WebSocket
    test_websocket_handshake(token)
    
    # Get debug info
    test_websocket_endpoint_info(token)
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main()