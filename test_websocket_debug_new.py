#!/usr/bin/env python3
"""Test WebSocket debug endpoints with new token"""

import urllib.request
import urllib.error
import json

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InNoYXJlZ3VhcmQuY29tXFxTaGFyZUd1YXJkU2VydmljZSIsImV4cCI6MTc1MTY2OTIwMSwiaWF0IjoxNzUxNTgyODAxfQ.54aWcVqlbhPx2gOLlBw3M33nqfZoKmzD0hMWn-rUlEk"

def test_endpoint(url, token=None, method="GET", data=None):
    try:
        req = urllib.request.Request(url, method=method)
        if token:
            req.add_header('Authorization', f'Bearer {token}')
        if data:
            req.data = json.dumps(data).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req) as response:
            return response.getcode(), response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return None, str(e)

print("Testing WebSocket-related endpoints")
print("=" * 50)

# Test WebSocket debug endpoint
print("\n1. WebSocket Debug Endpoint:")
status, body = test_endpoint("http://localhost:8000/api/v1/alerts/websocket-debug", TOKEN)
print(f"Status: {status}")
if status == 200:
    print(f"Response: {body}")
else:
    print(f"Error: {body}")

# Test monitoring status
print("\n2. Monitoring Status:")
status, body = test_endpoint("http://localhost:8000/api/v1/alerts/monitoring/status", TOKEN)
print(f"Status: {status}")
if status == 200:
    print(f"Response: {body}")
else:
    print(f"Error: {body}")

# Test sending a notification
print("\n3. Send Test Notification:")
status, body = test_endpoint(
    "http://localhost:8000/api/v1/alerts/test-notification",
    TOKEN,
    method="POST",
    data={"message": "Test from Python"}
)
print(f"Status: {status}")
print(f"Response: {body}")

# Let's check the logs directory
print("\n" + "=" * 50)
print("Checking for log files...")
import os
if os.path.exists('/mnt/c/ShareGuard/logs'):
    log_files = [f for f in os.listdir('/mnt/c/ShareGuard/logs') if f.endswith('.log')]
    if log_files:
        print("Found log files:")
        for f in log_files:
            print(f"  - logs/{f}")
        
        # Read last few lines of the most recent log
        most_recent = sorted(log_files)[-1]
        log_path = f'/mnt/c/ShareGuard/logs/{most_recent}'
        print(f"\nLast 20 lines of {most_recent}:")
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    if 'websocket' in line.lower() or 'alert' in line.lower():
                        print(line.strip())
        except Exception as e:
            print(f"Error reading log: {e}")
else:
    print("No logs directory found")