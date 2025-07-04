#!/usr/bin/env python3
"""Decode JWT token manually"""

import base64
import json
from datetime import datetime

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InNoYXJlZ3VhcmQuY29tXFxTaGFyZUd1YXJkU2VydmljZSIsImV4cCI6MTc1MTY2NjQwMSwiaWF0IjoxNzUxNTgwMDAxfQ.rkiw2vL9jxiFhIedmBpvyQxsKHE2JcjdvHvgYf5ehvo"

# Split the token
parts = TOKEN.split('.')

# Decode the payload (second part)
payload_encoded = parts[1]
# Add padding if needed
padding = 4 - len(payload_encoded) % 4
if padding != 4:
    payload_encoded += '=' * padding

payload_bytes = base64.urlsafe_b64decode(payload_encoded)
payload = json.loads(payload_bytes)

print("Token payload:")
print(json.dumps(payload, indent=2))

# Check expiration
if 'exp' in payload:
    exp_timestamp = payload['exp']
    exp_datetime = datetime.fromtimestamp(exp_timestamp)
    now = datetime.now()
    
    print(f"\nToken expires at: {exp_datetime}")
    print(f"Current time: {now}")
    
    if now > exp_datetime:
        print("❌ Token has EXPIRED!")
    else:
        time_left = exp_datetime - now
        print(f"✓ Token is still valid for: {time_left}")