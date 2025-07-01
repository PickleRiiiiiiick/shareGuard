#!/usr/bin/env python3
"""
Simple test to verify authentication with updated domain
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_login():
    """Test login with the updated domain"""
    auth_data = {
        "username": "ShareGuardService",
        "domain": "WIN-I2VDDDLDOUA",
        "password": r"P(5$\#SX07sj"  # Update this with the actual Windows password
    }
    
    print(f"Testing login with:")
    print(f"  Username: {auth_data['username']}")
    print(f"  Domain: {auth_data['domain']}")
    print(f"  API URL: {BASE_URL}/auth/login")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=auth_data,
            timeout=10
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Login SUCCESSFUL!")
            print(f"Token: {data['access_token'][:50]}...")
            print(f"Account: {data['account']}")
            return data['access_token']
        else:
            print("Login FAILED!")
            print(f"Error: {response.json()}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("\nERROR: Cannot connect to backend. Make sure it's running on port 8000.")
        return None
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return None

if __name__ == "__main__":
    print("ShareGuard Authentication Test")
    print("=" * 40)
    
    token = test_login()
    
    if token:
        print("\n✓ Authentication is working correctly!")
        print("\nIMPORTANT: Make sure the Windows user 'ShareGuardService' exists")
        print("and that you're using the correct password for that user.")
    else:
        print("\n✗ Authentication failed.")
        print("\nTroubleshooting steps:")
        print("1. Ensure the backend is running (python src/app.py)")
        print("2. Check that the Windows user 'ShareGuardService' exists")
        print("3. Verify the password is correct")
        print("4. Check logs/auth_routes_*.log for details")