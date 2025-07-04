#!/usr/bin/env python3
"""Check JWT token validity"""

import jwt
import json
from datetime import datetime

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InNoYXJlZ3VhcmQuY29tXFxTaGFyZUd1YXJkU2VydmljZSIsImV4cCI6MTc1MTY2NjQwMSwiaWF0IjoxNzUxNTgwMDAxfQ.rkiw2vL9jxiFhIedmBpvyQxsKHE2JcjdvHvgYf5ehvo"

# Decode without verification to see the payload
try:
    payload = jwt.decode(TOKEN, options={"verify_signature": False})
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
            
except Exception as e:
    print(f"Error decoding token: {e}")