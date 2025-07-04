#!/usr/bin/env python3
"""Test the new token from the frontend"""

import urllib.request
import json
from datetime import datetime
import base64

NEW_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InNoYXJlZ3VhcmQuY29tXFxTaGFyZUd1YXJkU2VydmljZSIsImV4cCI6MTc1MTY2OTIwMSwiaWF0IjoxNzUxNTgyODAxfQ.54aWcVqlbhPx2gOLlBw3M33nqfZoKmzD0hMWn-rUlEk"

# Decode token to check validity
def decode_token(token):
    parts = token.split('.')
    payload_encoded = parts[1]
    # Add padding if needed
    padding = 4 - len(payload_encoded) % 4
    if padding != 4:
        payload_encoded += '=' * padding
    
    payload_bytes = base64.urlsafe_b64decode(payload_encoded)
    return json.loads(payload_bytes)

# Test API endpoint with token
def test_api_with_token(token):
    try:
        url = "http://localhost:8000/api/v1/alerts?limit=1"
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {token}')
        
        with urllib.request.urlopen(req) as response:
            return response.getcode(), response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return None, str(e)

print("Testing new token from frontend")
print("=" * 50)

# Check token expiration
payload = decode_token(NEW_TOKEN)
print("Token payload:")
print(json.dumps(payload, indent=2))

exp_timestamp = payload['exp']
exp_datetime = datetime.fromtimestamp(exp_timestamp)
now = datetime.now()

print(f"\nToken expires at: {exp_datetime}")
print(f"Current time: {now}")

if now > exp_datetime:
    print("❌ Token has EXPIRED!")
else:
    time_left = exp_datetime - now
    print(f"✓ Token is valid for: {time_left}")

# Test API call
print("\nTesting API call with token...")
status, body = test_api_with_token(NEW_TOKEN)
print(f"Status: {status}")
if status == 200:
    print("✓ Token works for API calls!")
else:
    print(f"✗ API call failed: {body}")

# Test WebSocket with new token
print("\nTesting WebSocket connection with new token...")
import socket
from urllib.parse import urlencode

def test_websocket_with_token(token):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        sock.connect(("localhost", 8000))
        
        ws_key = base64.b64encode(b'1234567890123456').decode('utf-8')
        params = urlencode({"filters": "{}", "token": token})
        
        handshake = f"""GET /api/v1/alerts/notifications?{params} HTTP/1.1\r
Host: localhost:8000\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Key: {ws_key}\r
Sec-WebSocket-Version: 13\r
Origin: http://localhost:5173\r
\r
"""
        
        sock.send(handshake.encode())
        response = sock.recv(4096).decode('utf-8', errors='ignore')
        
        sock.close()
        return response
        
    except Exception as e:
        return f"Error: {e}"

ws_response = test_websocket_with_token(NEW_TOKEN)
print("WebSocket response:")
print(ws_response[:500])  # First 500 chars

print("\n" + "=" * 50)