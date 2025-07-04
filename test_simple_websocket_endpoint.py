#!/usr/bin/env python3
"""Test the simple WebSocket endpoint"""

import socket
import base64

def test_simple_websocket():
    """Test the /api/v1/alerts/test WebSocket endpoint"""
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
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        sock.send(handshake.encode())
        
        response = b""
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break
            response += chunk
            if b"\r\n\r\n" in response:
                break
                
        response_text = response.decode('utf-8', errors='ignore')
        
        print("Response:")
        print("-" * 40)
        print(response_text)
        print("-" * 40)
        
        if "101 Switching Protocols" in response_text:
            print("✓ Test WebSocket works!")
            
            # Try to read the "Hello WebSocket!" message
            try:
                sock.settimeout(3)
                message_data = sock.recv(1024)
                if message_data:
                    print(f"✓ Received data: {len(message_data)} bytes")
                    
                    # Try to decode WebSocket message
                    if len(message_data) >= 2:
                        opcode = message_data[0] & 0x0F
                        payload_len = message_data[1] & 0x7F
                        
                        if opcode == 1 and payload_len < 126:  # Text frame
                            payload = message_data[2:2+payload_len]
                            try:
                                text = payload.decode('utf-8')
                                print(f"✓ Message: '{text}'")
                            except:
                                print(f"✓ Binary data: {payload}")
            except socket.timeout:
                print("⚠ No message received")
                
        else:
            print("✗ Test WebSocket failed")
            
        sock.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_simple_websocket()