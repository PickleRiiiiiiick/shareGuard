#!/usr/bin/env python3
"""Direct WebSocket test with detailed error tracking"""

import socket
import base64
from urllib.parse import urlencode
import time

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InNoYXJlZ3VhcmQuY29tXFxTaGFyZUd1YXJkU2VydmljZSIsImV4cCI6MTc1MTY2OTIwMSwiaWF0IjoxNzUxNTgyODAxfQ.54aWcVqlbhPx2gOLlBw3M33nqfZoKmzD0hMWn-rUlEk"

def test_websocket():
    print("Direct WebSocket Connection Test")
    print("=" * 50)
    
    try:
        # 1. Create TCP connection
        print("\n1. Creating TCP socket...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # Longer timeout
        
        print("2. Connecting to localhost:8000...")
        sock.connect(("localhost", 8000))
        print("✓ TCP connection established")
        
        # 2. Send WebSocket upgrade request
        ws_key = base64.b64encode(b'1234567890123456').decode('utf-8')
        params = urlencode({"filters": "{}", "token": TOKEN})
        
        request = f"""GET /api/v1/alerts/notifications?{params} HTTP/1.1\r
Host: localhost:8000\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Key: {ws_key}\r
Sec-WebSocket-Version: 13\r
Origin: http://localhost:5173\r
User-Agent: Python-WebSocket-Test\r
Accept-Encoding: gzip, deflate, br\r
Accept-Language: en-US,en;q=0.9\r
\r
"""
        
        print("\n3. Sending WebSocket handshake...")
        print("Request (first 500 chars):")
        print(request[:500])
        
        sock.send(request.encode())
        
        # 3. Read response in chunks
        print("\n4. Reading response...")
        response = b""
        start_time = time.time()
        
        while time.time() - start_time < 5:  # 5 second timeout
            try:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                response += chunk
                
                # Check if we have complete headers
                if b"\r\n\r\n" in response:
                    headers_end = response.find(b"\r\n\r\n")
                    headers = response[:headers_end].decode('utf-8', errors='ignore')
                    print("\nResponse headers:")
                    print(headers)
                    
                    # Check for upgrade success
                    if "101 Switching Protocols" in headers:
                        print("\n✓ WebSocket upgrade successful!")
                        
                        # Try to read any initial messages
                        print("\n5. Waiting for initial messages...")
                        sock.settimeout(2)
                        try:
                            initial_msg = sock.recv(1024)
                            if initial_msg:
                                print(f"Received: {initial_msg}")
                        except socket.timeout:
                            print("No initial message received")
                    else:
                        print("\n✗ WebSocket upgrade failed")
                        
                        # Try to read error body
                        body_start = headers_end + 4
                        if len(response) > body_start:
                            body = response[body_start:].decode('utf-8', errors='ignore')
                            print(f"Error body: {body}")
                    break
                    
            except socket.timeout:
                break
        
        if not response:
            print("✗ No response received")
        
        sock.close()
        
    except ConnectionRefusedError:
        print("✗ Connection refused - backend not running")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_websocket()
    
    print("\n" + "=" * 50)
    print("Suggestions:")
    print("1. Check backend logs: tail -f logs/alert_routes_20250703.log")
    print("2. Check if notification service is initialized on startup")
    print("3. Verify CORS settings include ws://localhost:8000")
    print("4. Try restarting the backend with: .\\start-backend.ps1")