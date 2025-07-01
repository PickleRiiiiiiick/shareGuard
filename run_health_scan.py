#!/usr/bin/env python3
"""
Run a health scan via the API to analyze existing permission data
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"

def login():
    """Login and get auth token"""
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
                           json={"username": "admin", "password": "admin"})
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code}")
        return None

def run_health_scan(token):
    """Run health scan without specifying paths (will use existing data)"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Starting health scan...")
    response = requests.post(f"{BASE_URL}/api/v1/health/scan", 
                           headers=headers,
                           json={})  # Empty body, no target_paths
    
    if response.status_code == 200:
        result = response.json()
        print(f"Health scan status: {result['status']}")
        print(f"Message: {result['message']}")
        if 'target_paths' in result:
            print(f"Analyzing {len(result['target_paths'])} paths")
        return True
    else:
        print(f"Health scan failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def check_health_score(token):
    """Check current health score"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/v1/health/score", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"\nHealth Score: {data.get('score', 0)}")
        print(f"Total Issues: {data.get('issues', {}).get('total', 0)}")
        if 'last_scan' in data:
            print(f"Last Scan: {data['last_scan']}")
        return True
    else:
        print(f"Failed to get health score: {response.status_code}")
        return False

def main():
    """Main function"""
    print("ShareGuard Health Scan Runner")
    print("=" * 40)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("ERROR: Backend server is not running properly")
            print("Please start the server with: .\\start-backend.ps1")
            return 1
    except requests.exceptions.RequestException:
        print("ERROR: Cannot connect to backend server")
        print("Please start the server with: .\\start-backend.ps1")
        return 1
    
    # Login
    token = login()
    if not token:
        print("ERROR: Failed to authenticate")
        return 1
    
    print("Successfully authenticated")
    
    # Check initial health score
    print("\nChecking initial health score...")
    check_health_score(token)
    
    # Run health scan
    if run_health_scan(token):
        print("\nWaiting for scan to complete...")
        time.sleep(3)
        
        # Check updated health score
        print("\nChecking updated health score...")
        check_health_score(token)
        
        print("\nHealth scan completed successfully!")
        print("You can now view the results in the Health page of the web interface.")
    else:
        print("\nERROR: Health scan failed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())