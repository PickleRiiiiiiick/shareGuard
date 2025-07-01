#!/usr/bin/env python3
"""
Simple test script for health scan endpoint
"""
import sys
import os
import requests
import json

# Add src to path
sys.path.append('src')

BASE_URL = "http://localhost:8000/api/v1"

def test_authentication():
    """Test authentication and get token"""
    print("Testing authentication...")
    
    # Test credentials from the actual working credentials in logs
    login_data = {
        "username": "ShareGuardService",
        "password": "admin",
        "domain": "shareguard.com"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print("Authentication successful")
            return token
        else:
            print(f"Authentication failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"Authentication error: {e}")
        return None

def test_health_scan(token):
    """Test health scan endpoint"""
    print("Testing health scan...")
    
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    try:
        response = requests.post(f"{BASE_URL}/health/scan", headers=headers)
        print(f"Health scan response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 500:
            print("500 Internal Server Error detected - this is the issue!")
            print("Response headers:", dict(response.headers))
            
    except Exception as e:
        print(f"Health scan error: {e}")

def main():
    print("ShareGuard Health Scan Test")
    
    # Test authentication
    token = test_authentication()
    
    # Test health scan
    test_health_scan(token)

if __name__ == "__main__":
    main()