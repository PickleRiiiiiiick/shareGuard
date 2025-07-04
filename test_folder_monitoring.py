#!/usr/bin/env python3
"""Test folder monitoring and change detection"""

import sqlite3
import urllib.request
import json
import subprocess
import time
import os

def get_auth_token():
    """Get authentication token"""
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT token FROM auth_sessions 
            WHERE is_active = 1 
            ORDER BY created_at DESC 
            LIMIT 1;
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
    except:
        pass
    return None

def start_monitoring_with_scan_target_paths(token):
    """Start monitoring using paths from scan targets"""
    try:
        # Get scan target paths
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT path FROM scan_targets WHERE path IS NOT NULL;")
        targets = cursor.fetchall()
        conn.close()
        
        if not targets:
            print("⚠️ No scan targets with paths found")
            return False
        
        paths = [target[0] for target in targets]
        print(f"📁 Scan target paths: {paths}")
        
        # Start monitoring with explicit paths
        data = {"paths": paths}
        
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/alerts/monitoring/start",
            data=json.dumps(data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            
        print(f"✓ Monitoring started: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Error starting monitoring: {e}")
        return False

def check_monitoring_status(token):
    """Check monitoring status"""
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/alerts/monitoring/status",
            headers={'Authorization': f'Bearer {token}'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
        print("📊 Monitoring Status:")
        print(f"  Change monitoring active: {data.get('change_monitoring_active', False)}")
        print(f"  Monitored paths: {data.get('monitored_paths', [])}")
        
        stats = data.get('notification_service_stats', {})
        print(f"  Notification service stats:")
        print(f"    Active connections: {stats.get('active_connections', 0)}")
        print(f"    Notifications sent: {stats.get('notifications_sent', 0)}")
        
        return data
        
    except Exception as e:
        print(f"❌ Error checking monitoring status: {e}")
        return None

def create_folder_permission_change():
    """Create a real permission change on test folder"""
    test_path = "C:\\ShareGuardTest"
    
    try:
        if not os.path.exists(test_path):
            print(f"⚠️ Test folder {test_path} does not exist")
            return False
        
        print(f"🔄 Creating permission change on {test_path}...")
        
        # Grant Everyone read access
        cmd = ['icacls', test_path, '/grant', 'Everyone:R']
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            print(f"✓ Added Everyone:Read permission")
            print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"⚠️ Permission change failed: {result.stderr}")
            return False
        
        # Wait for monitoring to detect
        print("⏳ Waiting 15 seconds for change detection...")
        time.sleep(15)
        
        # Remove the permission
        cmd = ['icacls', test_path, '/remove', 'Everyone']
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            print(f"✓ Removed Everyone permission")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating permission change: {e}")
        return False

def check_for_new_changes():
    """Check database for new permission changes"""
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        # Check permission_changes table  
        cursor.execute("""
            SELECT id, change_type, detected_time, current_state
            FROM permission_changes 
            WHERE detected_time > datetime('now', '-30 minutes')
            ORDER BY detected_time DESC
            LIMIT 10;
        """)
        
        changes = cursor.fetchall()
        
        if changes:
            print(f"🎉 Found {len(changes)} recent permission changes!")
            for change in changes:
                change_id, change_type, detected_time, current_state = change
                print(f"  ID: {change_id}, Type: {change_type}")
                print(f"    Time: {detected_time}")
                if current_state:
                    try:
                        state = json.loads(current_state)
                        print(f"    Path: {state.get('path', 'N/A')}")
                    except:
                        pass
                print()
        else:
            print("⚠️ No recent permission changes detected")
        
        # Check for new alerts
        cursor.execute("""
            SELECT COUNT(*) FROM alerts 
            WHERE created_at > datetime('now', '-30 minutes');
        """)
        
        new_alerts = cursor.fetchone()[0]
        print(f"📊 New alerts in last 30 minutes: {new_alerts}")
        
        conn.close()
        return len(changes)
        
    except Exception as e:
        print(f"❌ Error checking changes: {e}")
        return 0

def main():
    print("ShareGuard Folder Monitoring Test")
    print("=" * 40)
    
    token = get_auth_token()
    if not token:
        print("❌ No authentication token available")
        return
    
    print("✓ Got authentication token")
    
    # Check current monitoring status
    print("\n[1] Checking current monitoring status...")
    status = check_monitoring_status(token)
    
    # Start monitoring with proper paths
    print("\n[2] Starting monitoring with scan target paths...")
    if start_monitoring_with_scan_target_paths(token):
        
        # Check status after starting
        print("\n[3] Checking monitoring status after start...")
        check_monitoring_status(token)
        
        # Create permission change
        print("\n[4] Creating folder permission change...")
        if create_folder_permission_change():
            
            # Check for detected changes
            print("\n[5] Checking for detected changes...")
            changes_found = check_for_new_changes()
            
            if changes_found > 0:
                print("\n🎉 SUCCESS: Change detection is working!")
                print("New alerts should appear in the UI within 10 seconds.")
            else:
                print("\n⚠️ No changes detected. Monitoring may not be working.")
                
    print("\n" + "=" * 40)
    print("Test completed!")
    print("\nNow refresh your browser to see:")
    print("1. Updated notification count") 
    print("2. Toast notifications (if polling is working)")
    print("3. New alerts in the list")

if __name__ == "__main__":
    main()