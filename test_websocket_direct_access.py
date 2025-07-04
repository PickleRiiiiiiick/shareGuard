#!/usr/bin/env python3
"""Test direct WebSocket access with proper headers"""

import socket
import base64
import urllib.parse
import hashlib

def create_websocket_accept_key(websocket_key):
    """Create the WebSocket accept key"""
    magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    combined = websocket_key + magic_string
    sha1_hash = hashlib.sha1(combined.encode()).digest()
    return base64.b64encode(sha1_hash).decode()

def test_websocket_handshake_detailed():
    """Test WebSocket handshake with detailed debugging"""
    print("Testing WebSocket handshake with detailed debugging...")
    
    host = "localhost"
    port = 8000
    
    # Create proper WebSocket key
    ws_key = base64.b64encode(b'1234567890123456').decode('utf-8')
    expected_accept = create_websocket_accept_key(ws_key)
    
    print(f"WebSocket Key: {ws_key}")
    print(f"Expected Accept: {expected_accept}")
    
    # Test with minimal required headers
    handshake = f"""GET /api/v1/alerts/notifications HTTP/1.1\r
Host: {host}:{port}\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Key: {ws_key}\r
Sec-WebSocket-Version: 13\r
\r
"""
    
    print(f"\nSending handshake:")
    print(handshake.replace('\r\n', '\\r\\n\n'))
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        sock.send(handshake.encode())
        
        # Receive response
        response = b""
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break
            response += chunk
            if b"\r\n\r\n" in response:
                break
                
        response_text = response.decode('utf-8', errors='ignore')
        
        print(f"\nReceived response:")
        print("-" * 50)
        print(response_text)
        print("-" * 50)
        
        # Parse response
        lines = response_text.split('\r\n')
        status_line = lines[0] if lines else ""
        
        if "101 Switching Protocols" in status_line:
            print("\n✓ WebSocket handshake successful!")
            
            # Check for correct accept key
            for line in lines[1:]:
                if line.lower().startswith('sec-websocket-accept:'):
                    received_accept = line.split(':', 1)[1].strip()
                    if received_accept == expected_accept:
                        print(f"✓ Correct WebSocket accept key: {received_accept}")
                    else:
                        print(f"✗ Wrong accept key. Expected: {expected_accept}, Got: {received_accept}")
                    break
            else:
                print("⚠ No WebSocket accept key in response")
                
        elif "404" in status_line:
            print("\n✗ WebSocket endpoint not found (404)")
        elif "403" in status_line:
            print("\n✗ WebSocket endpoint forbidden (403)")
        elif "401" in status_line:
            print("\n✗ Authentication required (401)")
        elif "426" in status_line:
            print("\n✓ Upgrade required (endpoint exists but needs proper headers)")
        else:
            print(f"\n? Unexpected status: {status_line}")
        
        sock.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")

def test_with_all_headers():
    """Test with all recommended WebSocket headers"""
    print("\n\nTesting with complete WebSocket headers...")
    
    host = "localhost" 
    port = 8000
    
    ws_key = base64.b64encode(b'1234567890123456').decode('utf-8')
    
    # Complete WebSocket handshake with all headers
    handshake = f"""GET /api/v1/alerts/notifications HTTP/1.1\r
Host: {host}:{port}\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Key: {ws_key}\r
Sec-WebSocket-Version: 13\r
Origin: http://localhost:5173\r
User-Agent: ShareGuard-Test/1.0\r
Cache-Control: no-cache\r
Pragma: no-cache\r
\r
"""
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        sock.send(handshake.encode())
        response = sock.recv(4096).decode('utf-8', errors='ignore')
        
        print(f"Response with complete headers:")
        print(response[:300] + "..." if len(response) > 300 else response)
        
        if "101 Switching Protocols" in response:
            print("✓ Success with complete headers")
        elif "404" in response:
            print("✗ Still 404 - route definitely not registered")
        elif "403" in response:
            print("✗ Still 403 - access denied")
        else:
            print("? Different response with complete headers")
            
        sock.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    print("ShareGuard WebSocket Direct Access Test")
    print("=" * 50)
    
    test_websocket_handshake_detailed()
    test_with_all_headers()
    
    print("\n" + "=" * 50)
    print("Test completed!")