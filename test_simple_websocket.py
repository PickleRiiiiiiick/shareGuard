#!/usr/bin/env python3
"""Test simple WebSocket endpoint"""

import socket
import base64
import hashlib

def create_websocket_accept_key(websocket_key):
    """Create the WebSocket accept key"""
    magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    combined = websocket_key + magic_string
    sha1_hash = hashlib.sha1(combined.encode()).digest()
    return base64.b64encode(sha1_hash).decode()

def test_simple_websocket():
    """Test the simple WebSocket test endpoint"""
    print("Testing simple WebSocket endpoint: /api/v1/alerts/test")
    
    host = "localhost"
    port = 8000
    
    ws_key = base64.b64encode(b'1234567890123456').decode('utf-8')
    
    handshake = f"""GET /api/v1/alerts/test HTTP/1.1\r
Host: {host}:{port}\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Key: {ws_key}\r
Sec-WebSocket-Version: 13\r
\r
"""
    
    print(f"Sending handshake to test endpoint...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        sock.send(handshake.encode())
        
        # Get response headers
        response = b""
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break
            response += chunk
            if b"\r\n\r\n" in response:
                break
                
        response_text = response.decode('utf-8', errors='ignore')
        
        print(f"Response:")
        print("-" * 40)
        print(response_text)
        print("-" * 40)
        
        if "101 Switching Protocols" in response_text:
            print("✓ WebSocket handshake successful!")
            
            # Try to read the "Hello WebSocket!" message
            try:
                sock.settimeout(2)
                message_data = sock.recv(1024)
                if message_data:
                    print(f"✓ Received WebSocket data: {len(message_data)} bytes")
                    
                    # Try to decode WebSocket frame (simplified)
                    if len(message_data) >= 2:
                        # Basic WebSocket frame parsing
                        # [FIN|RSV|Opcode][MASK|Payload Length][Payload]
                        opcode = message_data[0] & 0x0F
                        payload_len = message_data[1] & 0x7F
                        
                        if opcode == 1:  # Text frame
                            if payload_len < 126:
                                payload = message_data[2:2+payload_len]
                                try:
                                    text = payload.decode('utf-8')
                                    print(f"✓ WebSocket message: '{text}'")
                                except:
                                    print(f"✓ WebSocket binary data: {payload}")
                            else:
                                print(f"✓ WebSocket frame with extended length")
                        else:
                            print(f"✓ WebSocket frame with opcode: {opcode}")
                            
            except socket.timeout:
                print("⚠ No WebSocket message received")
                
        elif "403" in response_text:
            print("✗ Still getting 403 Forbidden")
        elif "404" in response_text:
            print("✗ Test endpoint not found")
        else:
            print("? Unexpected response")
            
        sock.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    print("ShareGuard Simple WebSocket Test")
    print("=" * 40)
    
    test_simple_websocket()
    
    print("\n" + "=" * 40)
    print("Test completed!")