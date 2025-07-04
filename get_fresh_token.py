#!/usr/bin/env python3
"""Get a fresh authentication token"""

import requests
import json

# Login endpoint
url = "http://localhost:8000/api/v1/auth/login"

# Default credentials from the codebase
payload = {
    "username": "shareguard.com\\ShareGuardService",
    "password": "P@ssw0rd123!"
}

try:
    print("Attempting to login...")
    response = requests.post(url, json=payload)
    
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\nLogin successful!")
        print(f"Token: {data['token']}")
        print(f"\nUse this fresh token in your WebSocket connection")
        
        # Save to file for easy access
        with open('fresh_token.txt', 'w') as f:
            f.write(data['token'])
        print("\nToken saved to fresh_token.txt")
    else:
        print(f"Login failed: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to backend. Make sure it's running on localhost:8000")
except Exception as e:
    print(f"Error: {e}")