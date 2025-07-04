#!/usr/bin/env python3
"""Get a fresh authentication token using urllib"""

import urllib.request
import urllib.parse
import json

# Login endpoint
url = "http://localhost:8000/api/v1/auth/login"

# Default credentials from the codebase
# Split domain and username
full_username = "shareguard.com\\ShareGuardService"
domain, username = full_username.split('\\')

payload = {
    "username": username,
    "domain": domain,
    "password": "P@ssw0rd123!"
}

try:
    print("Attempting to login...")
    
    # Prepare the request
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    req.add_header('Content-Type', 'application/json')
    
    # Send the request
    with urllib.request.urlopen(req) as response:
        status_code = response.getcode()
        print(f"Status code: {status_code}")
        
        if status_code == 200:
            data = json.loads(response.read().decode('utf-8'))
            print("\nLogin successful!")
            print(f"Token: {data['token']}")
            print(f"\nUse this fresh token in your WebSocket connection")
            
            # Save to file for easy access
            with open('fresh_token.txt', 'w') as f:
                f.write(data['token'])
            print("\nToken saved to fresh_token.txt")
        
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.reason}")
    print(f"Response: {e.read().decode('utf-8')}")
except urllib.error.URLError as e:
    print("Error: Could not connect to backend. Make sure it's running on localhost:8000")
    print(f"Details: {e}")
except Exception as e:
    print(f"Error: {e}")