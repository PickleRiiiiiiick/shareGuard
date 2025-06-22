#!/usr/bin/env python3
"""
Test SID resolution through the API endpoints.
This script tests the SID resolution by calling the API directly.
"""

import requests
import json
import sys
import os

def test_sid_resolution_via_api(base_url="http://localhost:8000", test_path="C:\\ShareGuardTest"):
    """Test SID resolution using the API endpoints."""
    
    print("Testing SID Resolution via API")
    print("=" * 50)
    print(f"Base URL: {base_url}")
    print(f"Test Path: {test_path}")
    print()
    
    # You'll need to authenticate first - get your auth token
    auth_token = input("Enter your auth token (from browser dev tools or login): ").strip()
    
    if not auth_token:
        print("No auth token provided. Please log in to the web interface first.")
        print("1. Open http://localhost:5173 in your browser")
        print("2. Log in")
        print("3. Open browser dev tools (F12)")
        print("4. Go to Application/Storage > Local Storage")
        print("5. Copy the 'auth_token' value")
        return
    
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Test 1: Get folder permissions
        print("Test 1: Getting folder permissions...")
        response = requests.get(
            f"{base_url}/api/v1/folders/permissions",
            params={'path': test_path, 'include_inherited': 'true'},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            permissions = data.get('permissions', {})
            aces = permissions.get('aces', [])
            
            print(f"✓ Successfully retrieved {len(aces)} ACEs")
            
            # Analyze SID resolution
            unknown_count = 0
            resolved_count = 0
            
            print("\nACE Analysis:")
            print("-" * 40)
            
            for i, ace in enumerate(aces[:5]):  # Show first 5 ACEs
                trustee = ace.get('trustee', {})
                name = trustee.get('name', 'N/A')
                domain = trustee.get('domain', 'N/A')
                sid = trustee.get('sid', 'N/A')
                account_type = trustee.get('account_type', 'N/A')
                
                if name == "Unknown":
                    unknown_count += 1
                    status = "❌ UNKNOWN"
                else:
                    resolved_count += 1
                    status = "✓ RESOLVED"
                
                print(f"ACE {i+1}: {status}")
                print(f"  Name: {name}")
                print(f"  Domain: {domain}")
                print(f"  SID: {sid}")
                print(f"  Type: {account_type}")
                print(f"  Full: {trustee.get('full_name', 'N/A')}")
                print()
            
            total_unknown = sum(1 for ace in aces if ace.get('trustee', {}).get('name') == "Unknown")
            total_resolved = len(aces) - total_unknown
            
            print(f"Summary: {total_resolved} resolved, {total_unknown} unknown out of {len(aces)} total")
            
        else:
            print(f"❌ Failed to get permissions: {response.status_code}")
            print(f"Response: {response.text}")
        
        # Test 2: Use diagnostic endpoint
        print("\n" + "=" * 50)
        print("Test 2: Using diagnostic endpoint...")
        
        response = requests.get(
            f"{base_url}/api/v1/folders/diagnose-sids",
            params={'path': test_path},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            diagnosis = data.get('diagnosis', {})
            
            print("✓ Diagnostic completed")
            print(f"Total ACEs: {diagnosis.get('total_aces', 0)}")
            print(f"Resolved: {diagnosis.get('resolved_count', 0)}")
            print(f"Unknown: {diagnosis.get('unknown_count', 0)}")
            
            problematic_sids = diagnosis.get('problematic_sids', [])
            if problematic_sids:
                print(f"\nProblematic SIDs ({len(problematic_sids)}):")
                for sid_info in problematic_sids[:3]:  # Show first 3
                    print(f"  SID: {sid_info.get('sid')}")
                    print(f"  Full Name: {sid_info.get('full_name')}")
                    print()
            
        else:
            print(f"❌ Diagnostic failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the backend is running:")
        print("  Run: .\\start-backend.ps1")
        print("  Or: python -m uvicorn src.app:app --reload")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def simple_test_without_auth():
    """Test basic functionality without authentication."""
    print("Simple Test - Checking if backend is running...")
    
    try:
        response = requests.get("http://localhost:8000/docs")
        if response.status_code == 200:
            print("✓ Backend is running at http://localhost:8000")
            print("✓ API docs available at http://localhost:8000/docs")
        else:
            print(f"❓ Backend responded with status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running")
        print("Start it with: .\\start-backend.ps1")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
    else:
        test_path = "C:\\ShareGuardTest"
    
    print("ShareGuard SID Resolution API Test")
    print("=" * 40)
    
    # First check if backend is running
    simple_test_without_auth()
    print()
    
    # Ask user if they want to proceed with full test
    proceed = input("Do you want to run the full API test? (y/n): ").strip().lower()
    if proceed == 'y':
        test_sid_resolution_via_api(test_path=test_path)
    else:
        print("\nTo run the full test later:")
        print("1. Make sure backend is running: .\\start-backend.ps1")
        print("2. Log in to web interface: http://localhost:5173") 
        print("3. Run: python test_sid_via_api.py")