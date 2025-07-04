#!/usr/bin/env python3
"""Test WebSocket connection and debugging endpoints"""

import urllib.request
import urllib.parse
import json

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InNoYXJlZ3VhcmQuY29tXFxTaGFyZUd1YXJkU2VydmljZSIsImV4cCI6MTc1MTY2NjQwMSwiaWF0IjoxNzUxNTgwMDAxfQ.rkiw2vL9jxiFhIedmBpvyQxsKHE2JcjdvHvgYf5ehvo"

def test_endpoint(url, token=None, method="GET", data=None):
    """Test an HTTP endpoint"""
    try:
        req = urllib.request.Request(url, method=method)
        if token:
            req.add_header('Authorization', f'Bearer {token}')
        if data:
            req.data = json.dumps(data).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            return status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return None, str(e)

print("ShareGuard WebSocket Debug Test")
print("=" * 50)

# Test 1: Check WebSocket debug endpoint
print("\n1. Testing WebSocket debug endpoint...")
status, body = test_endpoint("http://localhost:8000/api/v1/alerts/websocket-debug", TOKEN)
print(f"Status: {status}")
if status == 200:
    data = json.loads(body)
    print(f"WebSocket stats: {json.dumps(data, indent=2)}")
else:
    print(f"Error: {body}")

# Test 2: Check monitoring status
print("\n2. Testing monitoring status...")
status, body = test_endpoint("http://localhost:8000/api/v1/alerts/monitoring/status", TOKEN)
print(f"Status: {status}")
if status == 200:
    data = json.loads(body)
    print(f"Monitoring status: {json.dumps(data, indent=2)}")
else:
    print(f"Error: {body}")

# Test 3: Send test notification
print("\n3. Sending test notification...")
status, body = test_endpoint(
    "http://localhost:8000/api/v1/alerts/test-notification",
    TOKEN,
    method="POST",
    data={"message": "Test from Python script"}
)
print(f"Status: {status}")
if status == 200:
    data = json.loads(body)
    print(f"Result: {json.dumps(data, indent=2)}")
else:
    print(f"Error: {body}")

# Test 4: Check if token is valid by getting alerts
print("\n4. Testing token validity (getting alerts)...")
status, body = test_endpoint("http://localhost:8000/api/v1/alerts?limit=1", TOKEN)
print(f"Status: {status}")
if status == 200:
    print("✓ Token is valid and working for API calls")
else:
    print(f"✗ Token validation failed: {body}")

print("\n" + "=" * 50)
print("Debug test completed!")