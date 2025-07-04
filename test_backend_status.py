#!/usr/bin/env python3
"""Test backend status and available endpoints"""

import urllib.request
import urllib.error
import json

def test_endpoint(url, token=None):
    try:
        req = urllib.request.Request(url)
        if token:
            req.add_header('Authorization', f'Bearer {token}')
        with urllib.request.urlopen(req) as response:
            return response.getcode(), response.read().decode('utf-8')[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')[:200]
    except Exception as e:
        return None, str(e)

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InNoYXJlZ3VhcmQuY29tXFxTaGFyZUd1YXJkU2VydmljZSIsImV4cCI6MTc1MTY2OTIwMSwiaWF0IjoxNzUxNTgyODAxfQ.54aWcVqlbhPx2gOLlBw3M33nqfZoKmzD0hMWn-rUlEk"

print("Testing backend endpoints")
print("=" * 50)

# Test various endpoints
endpoints = [
    ("Root", "http://localhost:8000/"),
    ("Docs", "http://localhost:8000/docs"),
    ("OpenAPI", "http://localhost:8000/openapi.json"),
    ("Health", "http://localhost:8000/api/v1/health"),
    ("Auth Test", "http://localhost:8000/api/v1/auth/test"),
    ("Scan Targets", "http://localhost:8000/api/v1/targets"),
    ("Alerts", "http://localhost:8000/api/v1/alerts"),
    ("Alert Configs", "http://localhost:8000/api/v1/alerts/configurations"),
]

for name, url in endpoints:
    print(f"\n{name}: {url}")
    status, body = test_endpoint(url, TOKEN if "api/v1" in url else None)
    print(f"Status: {status}")
    if status and status < 400:
        print(f"Response: {body}")
    else:
        print(f"Error: {body}")

# Check backend logs location
print("\n" + "=" * 50)
print("Backend logs might be in:")
print("- logs/shareguard.log")
print("- logs/shareguard_YYYY-MM-DD.log")
print("\nRun: tail -f logs/shareguard_*.log")
print("to see real-time backend logs while testing WebSocket")