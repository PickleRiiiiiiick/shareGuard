#!/usr/bin/env python3
"""Test WebSocket authentication fix"""

import socket
import base64
import urllib.parse
import json

def test_websocket_auth_bypass():
    """Test if WebSocket endpoint now bypasses auth middleware"""
    print("Testing WebSocket authentication fix...")
    
    host = "localhost"
    port = 8000
    
    # Create WebSocket key
    ws_key = base64.b64encode(b'1234567890123456').decode('utf-8')
    
    # Test 1: No token (should fail at WebSocket level, not middleware level)
    print("\n[1] Testing without token...")
    params = urllib.parse.urlencode({"filters": "{}"})
    
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
        print(response[:200] + "..." if len(response) > 200 else response)
        
        if "101 Switching Protocols" in response:
            print("✓ WebSocket upgrade successful (auth middleware bypassed)")
            
            # Try to read WebSocket close frame
            try:
                sock.settimeout(2)
                close_data = sock.recv(1024)
                if close_data:
                    # WebSocket close frame format: [FIN+opcode][payload_len][close_code][reason]
                    if len(close_data) >= 4:
                        close_code = (close_data[2] << 8) | close_data[3]
                        print(f"✓ WebSocket closed with code: {close_code}")
                        if close_code == 1008:
                            print("✓ Expected auth failure at WebSocket level (not middleware)")
                        else:
                            print(f"? Unexpected close code: {close_code}")
            except socket.timeout:
                print("⚠ No close frame received")
                
        elif "401" in response and "Authentication required" in response:
            print("✗ Still blocked by auth middleware")
        else:
            print(f"? Unexpected response")
            
        sock.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: With dummy token (should reach WebSocket handler)
    print("\n[2] Testing with dummy token...")
    dummy_token = "dummy.token.here"
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
        print(response[:200] + "..." if len(response) > 200 else response)
        
        if "101 Switching Protocols" in response:
            print("✓ WebSocket upgrade successful with dummy token")
            print("✓ Auth middleware bypass working!")
            
            # Try to read close frame for auth failure
            try:
                sock.settimeout(2)
                close_data = sock.recv(1024)
                if close_data and len(close_data) >= 4:
                    close_code = (close_data[2] << 8) | close_data[3]
                    print(f"✓ WebSocket auth failed as expected: {close_code}")
            except socket.timeout:
                print("⚠ No close frame received")
                
        elif "401" in response:
            print("✗ Still blocked by auth middleware")
        else:
            print(f"? Unexpected response")
            
        sock.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")

def test_regular_api_still_protected():
    """Ensure regular API endpoints still require auth"""
    print("\n[3] Testing that regular API endpoints still require auth...")
    
    import urllib.request
    
    try:
        req = urllib.request.Request("http://localhost:8000/api/v1/alerts/")
        with urllib.request.urlopen(req) as response:
            print("✗ Regular API endpoint not protected!")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("✓ Regular API endpoint still protected")
        else:
            print(f"? Unexpected status: {e.code}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    print("ShareGuard WebSocket Authentication Fix Test")
    print("=" * 50)
    
    test_websocket_auth_bypass()
    test_regular_api_still_protected()
    
    print("\n" + "=" * 50)
    print("Test completed!")