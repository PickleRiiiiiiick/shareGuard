#!/usr/bin/env python3
import requests
import json

def start_monitoring():
    """Start monitoring via API"""
    base_url = "http://localhost:8000/api/v1"
    
    try:
        # 1. Get authentication token
        print("1. Getting authentication token...")
        auth_data = {
            "username": "admin", 
            "password": "admin123"
        }
        
        auth_response = requests.post(
            f"{base_url}/auth/token",
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if auth_response.status_code != 200:
            print(f"   ❌ Authentication failed: {auth_response.status_code}")
            print(f"   Response: {auth_response.text}")
            return
        
        token_data = auth_response.json()
        if "access_token" in token_data:
            token = token_data["access_token"]
        else:
            print(f"   ❌ No access_token in response: {token_data}")
            return
        
        print(f"   ✅ Authentication successful")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Check monitoring status
        print("\n2. Checking monitoring status...")
        status_response = requests.get(f"{base_url}/alerts/monitoring/status", headers=headers)
        
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"   Monitoring active: {status.get('change_monitoring_active', False)}")
            print(f"   Monitored paths: {status.get('monitored_paths', [])}")
        else:
            print(f"   ❌ Status check failed: {status_response.status_code}")
        
        # 3. Start monitoring
        print("\n3. Starting monitoring...")
        start_response = requests.post(f"{base_url}/alerts/monitoring/start", headers=headers)
        
        if start_response.status_code == 200:
            result = start_response.json()
            print(f"   ✅ Monitoring started successfully!")
            print(f"   Message: {result.get('message')}")
            print(f"   Paths: {result.get('monitoring_paths', [])}")
            print(f"   Path count: {result.get('path_count', 0)}")
        else:
            print(f"   ❌ Failed to start monitoring: {start_response.status_code}")
            print(f"   Response: {start_response.text}")
        
        # 4. Verify monitoring is active
        print("\n4. Verifying monitoring is active...")
        status_response = requests.get(f"{base_url}/alerts/monitoring/status", headers=headers)
        
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"   Monitoring active: {status.get('change_monitoring_active', False)}")
            print(f"   Monitored paths: {status.get('monitored_paths', [])}")
            
            if status.get('change_monitoring_active'):
                print(f"\n🎉 SUCCESS: Monitoring is now active!")
                print(f"📁 Monitoring {len(status.get('monitored_paths', []))} paths")
                print(f"⏰ Changes will be detected every 60 seconds")
                print(f"📱 Alerts will appear in the UI immediately")
            else:
                print(f"\n⚠️ Monitoring is not active")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    start_monitoring()