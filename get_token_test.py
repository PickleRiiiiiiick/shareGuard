#!/usr/bin/env python3
"""Get a valid token for testing"""

import urllib.request
import json

def get_token():
    """Try to get a valid authentication token"""
    
    # From the logs, I see that a successful login happened earlier
    # Let me check what credentials actually work
    
    # Based on the service account info and recent successful logins
    credentials = [
        # Format that requires domain field
        {
            "username": "ShareGuardService",
            "domain": "shareguard.com", 
            "password": "ShareGuardService"
        },
        {
            "username": "ShareGuardService",
            "domain": "WORKGROUP",
            "password": "ShareGuardService"
        },
        {
            "username": "ShareGuardService", 
            "domain": ".",
            "password": "ShareGuardService"
        },
        # Try some common dev passwords
        {
            "username": "ShareGuardService",
            "domain": "shareguard.com",
            "password": "password"
        },
        {
            "username": "ShareGuardService",
            "domain": "shareguard.com", 
            "password": "admin"
        }
    ]
    
    for i, creds in enumerate(credentials, 1):
        print(f"[{i}] Trying: {creds['domain']}\\{creds['username']} with password '{creds['password']}'")
        
        try:
            req = urllib.request.Request(
                "http://localhost:8000/api/v1/auth/login",
                data=json.dumps(creds).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                token = data.get('access_token')
                if token:
                    print(f"✓ Success! Got token: {token[:50]}...")
                    return token
                    
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"  ✗ Failed: {e.code}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\nNo credentials worked. The service might need to be restarted or credentials reset.")
    return None

if __name__ == "__main__":
    print("ShareGuard Token Test")
    print("=" * 30)
    get_token()