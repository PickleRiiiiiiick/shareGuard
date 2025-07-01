#!/usr/bin/env python3
"""
Test script for health endpoints.
This script tests the health API endpoints to ensure they're working correctly.
"""

import sys
import os
import requests
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

BASE_URL = "http://localhost:8000/api/v1/health"

def get_auth_token():
    """Get authentication token for API requests."""
    try:
        # Try to authenticate with default credentials
        auth_response = requests.post("http://localhost:8000/api/v1/auth/login", 
                                    json={"username": "admin", "password": "admin"},
                                    headers={"Content-Type": "application/json"})
        
        if auth_response.status_code == 200:
            token_data = auth_response.json()
            return token_data.get("access_token")
        else:
            logger.warning(f"Authentication failed with status {auth_response.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Authentication failed: {str(e)}")
        return None

def test_health_score(headers=None):
    """Test the health score endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/score", headers=headers or {})
        logger.info(f"Health score endpoint - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("OK Health score endpoint working")
            print(f"   Score: {data.get('score', 'N/A')}")
            print(f"   Issues: {data.get('issues', {})}")
            if 'error' in data:
                print(f"   Note: {data['error']}")
            if 'message' in data:
                print(f"   Message: {data['message']}")
            return True
        else:
            print(f"FAIL Health score endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR Health score endpoint error: {str(e)}")
        return False

def test_health_issues(headers=None):
    """Test the health issues endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/issues", headers=headers or {})
        logger.info(f"Health issues endpoint - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("OK Health issues endpoint working")
            print(f"   Total issues: {data.get('total', 0)}")
            print(f"   Issues returned: {len(data.get('issues', []))}")
            if 'error' in data:
                print(f"   Note: {data['error']}")
            return True
        else:
            print(f"FAIL Health issues endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR Health issues endpoint error: {str(e)}")
        return False

def test_server_connection():
    """Test if the server is running."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("OK Server is running")
            return True
        else:
            print(f"FAIL Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR Cannot connect to server: {str(e)}")
        print("   Make sure the ShareGuard backend is running on localhost:8000")
        return False

def main():
    """Run all health endpoint tests."""
    print("ShareGuard Health Endpoints Test")
    print("=" * 40)
    
    # Test server connection
    if not test_server_connection():
        print("\nTo start the server, run: ./start-backend.ps1")
        return False
    
    # Get authentication token
    print("\nAttempting authentication...")
    token = get_auth_token()
    headers = {}
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        print("OK Authentication successful")
    else:
        print("WARNING Authentication failed, testing without auth")
    
    print("\nTesting health endpoints...")
    
    # Test endpoints
    score_ok = test_health_score(headers)
    issues_ok = test_health_issues(headers)
    
    print("\n" + "=" * 40)
    if score_ok and issues_ok:
        print("SUCCESS All health endpoints are working!")
        print("\nIf you see error messages in the responses, try running:")
        print("   python init_health_tables.py")
        return True
    else:
        print("FAIL Some health endpoints are not working")
        print("\nTroubleshooting steps:")
        print("   1. Make sure the backend server is running")
        print("   2. Run: python init_health_tables.py")
        print("   3. Check the backend logs for errors")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)