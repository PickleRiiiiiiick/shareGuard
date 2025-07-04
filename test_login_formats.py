#!/usr/bin/env python3
"""Test different login payload formats"""

import urllib.request
import json

BASE_URL = "http://localhost:8000"

def test_login(payload_desc, payload):
    """Test a login payload"""
    print(f"\nTesting: {payload_desc}")
    print(f"Payload: {json.dumps(payload)}")
    
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/auth/login",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("✓ Success!")
            print(f"  Token: {data.get('access_token', 'N/A')[:50]}...")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"✗ Failed: {e.code} - {e.reason}")
        try:
            error_data = json.loads(error_body)
            if 'detail' in error_data:
                print(f"  Detail: {error_data['detail']}")
        except:
            print(f"  Body: {error_body}")
        return False
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        return False

print("ShareGuard Login Format Test")
print("=" * 50)

# Test different formats
payloads = [
    ("Format 1: username/domain/password", {
        "username": "ShareGuardService",
        "domain": "shareguard.com",
        "password": "ShareGuardService"
    }),
    ("Format 2: domain\\username in username field", {
        "username": "shareguard.com\\ShareGuardService",
        "password": "ShareGuardService"
    }),
    ("Format 3: With P@ssw0rd123!", {
        "username": "ShareGuardService",
        "domain": "shareguard.com",
        "password": "P@ssw0rd123!"
    }),
    ("Format 4: domain\\username with P@ssw0rd123!", {
        "username": "shareguard.com\\ShareGuardService",
        "password": "P@ssw0rd123!"
    }),
]

for desc, payload in payloads:
    test_login(desc, payload)