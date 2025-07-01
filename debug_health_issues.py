#!/usr/bin/env python3
"""
Debug script for ShareGuard Health page issues
Helps identify root causes of:
1. Health score not loading
2. CSV export 422 errors 
3. Health scan not updating data
"""

import sys
import os
import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_authentication():
    """Test authentication and get token"""
    print_section("AUTHENTICATION TEST")
    
    # Test credentials (you may need to adjust these)
    login_data = {
        "username": "admin",  # Adjust as needed
        "password": "admin"   # Adjust as needed
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"✅ Authentication successful")
            print(f"Token: {token[:50]}..." if token else "❌ No token received")
            return token
        else:
            print(f"❌ Authentication failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_health_score(token):
    """Test health score endpoint"""
    print_section("HEALTH SCORE TEST")
    
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    try:
        response = requests.get(f"{BASE_URL}/health/score", headers=headers)
        print(f"Health score response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health score retrieved successfully")
            print(f"Data structure: {json.dumps(data, indent=2)}")
            
            # Check if data has expected structure
            if 'issueCountBySeverity' in data:
                print(f"✅ Has issueCountBySeverity: {data['issueCountBySeverity']}")
            else:
                print(f"❌ Missing issueCountBySeverity")
                
            if 'issueCountByType' in data:
                print(f"✅ Has issueCountByType: {data['issueCountByType']}")
            else:
                print(f"❌ Missing issueCountByType")
                
        elif response.status_code == 401:
            print(f"❌ Authentication required (401): {response.text}")
        else:
            print(f"❌ Health score failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Health score error: {e}")

def test_health_issues(token):
    """Test health issues endpoint"""
    print_section("HEALTH ISSUES TEST")
    
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    try:
        response = requests.get(f"{BASE_URL}/health/issues", headers=headers)
        print(f"Health issues response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health issues retrieved successfully")
            print(f"Issues count: {len(data.get('issues', []))}")
            print(f"Total: {data.get('total', 0)}")
        elif response.status_code == 401:
            print(f"❌ Authentication required (401): {response.text}")
        else:
            print(f"❌ Health issues failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Health issues error: {e}")

def test_health_export(token):
    """Test health export endpoint"""
    print_section("HEALTH EXPORT TEST")
    
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    # Test different parameter combinations
    test_cases = [
        {"format": "csv"},
        {"format": "csv", "severity": "high"},
        {"format": "csv", "issue_type": "overprivileged"},
        {"format": "csv", "path_filter": "test"},
    ]
    
    for i, params in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {params}")
        try:
            response = requests.get(f"{BASE_URL}/health/issues/export", 
                                  headers=headers, params=params)
            print(f"Export response status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Export successful")
                print(f"Content-Type: {response.headers.get('content-type')}")
                print(f"Content length: {len(response.content)} bytes")
            elif response.status_code == 401:
                print(f"❌ Authentication required (401): {response.text}")
            elif response.status_code == 422:
                print(f"❌ Validation error (422): {response.text}")
            else:
                print(f"❌ Export failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Export error: {e}")

def test_health_scan(token):
    """Test health scan endpoint"""
    print_section("HEALTH SCAN TEST")
    
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    try:
        response = requests.post(f"{BASE_URL}/health/scan", headers=headers)
        print(f"Health scan response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health scan started successfully")
            print(f"Response: {json.dumps(data, indent=2)}")
        elif response.status_code == 401:
            print(f"❌ Authentication required (401): {response.text}")
        else:
            print(f"❌ Health scan failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Health scan error: {e}")

def check_database_tables():
    """Check if health tables exist in database"""
    print_section("DATABASE TABLES CHECK")
    
    try:
        # This would require database connection, which might be complex
        # For now, we'll suggest manual checking
        print("To check database tables manually, run:")
        print("1. Connect to your SQL Server database")
        print("2. Run: SELECT name FROM sys.tables WHERE name LIKE '%health%' OR name LIKE '%issue%'")
        print("3. Expected tables: health_scans, issues, health_metrics, health_score_history")
        
    except Exception as e:
        print(f"❌ Database check error: {e}")

def main():
    print(f"ShareGuard Health Debug Script")
    print(f"Started at: {datetime.now()}")
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running (FastAPI docs accessible)")
        else:
            print("⚠️  Backend may be running but docs not accessible")
    except Exception as e:
        print(f"❌ Backend appears to be down: {e}")
        print("Please start the backend first using: python -m uvicorn app:app --reload")
        return
    
    # Test authentication
    token = test_authentication()
    
    # Run all tests
    test_health_score(token)
    test_health_issues(token)
    test_health_export(token)
    test_health_scan(token)
    check_database_tables()
    
    print_section("SUMMARY")
    print("Check the logs above for specific issues.")
    print("Common fixes:")
    print("1. If auth fails: Check credentials in script")
    print("2. If health data missing: Run health scan first")
    print("3. If 422 errors: Check parameter validation")
    print("4. If tables missing: Run 'python init_health_tables.py'")

if __name__ == "__main__":
    main()