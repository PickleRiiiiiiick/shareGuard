#!/usr/bin/env python3
"""Set up test monitoring and create a test change"""

import sqlite3
import urllib.request
import json
import os
import subprocess
import time

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

def check_scan_targets():
    """Check scan targets table structure and data"""
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        # Get table structure
        cursor.execute("PRAGMA table_info(scan_targets);")
        columns = cursor.fetchall()
        
        print("📊 Scan targets table structure:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Get all scan targets
        cursor.execute("SELECT * FROM scan_targets ORDER BY created_at DESC;")
        targets = cursor.fetchall()
        
        print(f"\n📊 Found {len(targets)} scan targets:")
        for target in targets:
            print(f"  Target: {target}")
        
        conn.close()
        return targets
        
    except Exception as e:
        print(f"❌ Error checking scan targets: {e}")
        return []

def create_test_folder():
    """Create test folder for permission monitoring"""
    test_path = "C:\\ShareGuardTest"
    
    try:
        if not os.path.exists(test_path):
            os.makedirs(test_path, exist_ok=True)
            print(f"✓ Created test folder: {test_path}")
        else:
            print(f"✓ Test folder exists: {test_path}")
        
        # Create a test file
        test_file = os.path.join(test_path, "test_file.txt")
        if not os.path.exists(test_file):
            with open(test_file, 'w') as f:
                f.write("Test file for ShareGuard monitoring\n")
            print(f"✓ Created test file: {test_file}")
        
        return test_path
        
    except Exception as e:
        print(f"❌ Error creating test folder: {e}")
        return None

def add_scan_target_via_api(token, path):
    """Add scan target via API"""
    try:
        data = {
            "name": "ShareGuard Test Folder",
            "path": path,
            "description": "Test folder for monitoring permission changes"
        }
        
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/targets/",
            data=json.dumps(data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            
        print(f"✓ Added scan target: {result.get('name')} (ID: {result.get('id')})")
        return result.get('id')
        
    except Exception as e:
        print(f"❌ Error adding scan target: {e}")
        return None

def start_monitoring(token):
    """Start monitoring via API"""
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/alerts/monitoring/start",
            data=b'{}',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            
        print(f"✓ Started monitoring: {result.get('message')}")
        return True
        
    except Exception as e:
        print(f"❌ Error starting monitoring: {e}")
        return False

def create_permission_change(test_path):
    """Create a permission change to test detection"""
    try:
        print(f"\n🔄 Creating permission change on {test_path}...")
        
        # Use icacls to grant Everyone read access (Windows command)
        cmd = f'icacls "{test_path}" /grant Everyone:R'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Added Everyone:Read permission")
        else:
            print(f"⚠️ Permission change command result: {result.stderr}")
        
        # Wait a moment
        time.sleep(2)
        
        # Remove the permission
        cmd = f'icacls "{test_path}" /remove Everyone'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Removed Everyone permission")
        else:
            print(f"⚠️ Permission removal command result: {result.stderr}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating permission change: {e}")
        return False

def check_for_changes_after_test():
    """Check database for changes after test"""
    print(f"\n⏳ Waiting 10 seconds for changes to be detected...")
    time.sleep(10)
    
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        # Check for recent permission changes
        cursor.execute("""
            SELECT id, change_type, detected_time, current_state
            FROM permission_changes 
            WHERE detected_time > datetime('now', '-1 hour')
            ORDER BY detected_time DESC;
        """)
        
        changes = cursor.fetchall()
        
        if changes:
            print(f"🎉 Found {len(changes)} new permission changes!")
            for change in changes:
                change_id, change_type, detected_time, curr_state = change
                print(f"  ID: {change_id}, Type: {change_type}, Time: {detected_time}")
        else:
            print("⚠️ No new permission changes detected")
        
        # Check for alerts
        cursor.execute("""
            SELECT id, severity, message, created_at
            FROM alerts 
            WHERE created_at > datetime('now', '-1 hour')
            ORDER BY created_at DESC;
        """)
        
        alerts = cursor.fetchall()
        
        if alerts:
            print(f"🔔 Found {len(alerts)} new alerts!")
            for alert in alerts:
                alert_id, severity, message, created_at = alert
                print(f"  ID: {alert_id}, Severity: {severity}")
                print(f"    Message: {message}")
        else:
            print("⚠️ No new alerts generated")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking for changes: {e}")

def main():
    print("ShareGuard Test Monitoring Setup")
    print("=" * 40)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ No authentication token available")
        return
    
    print("✓ Got authentication token")
    
    # Check current scan targets
    print("\n[1] Checking current scan targets...")
    check_scan_targets()
    
    # Create test folder
    print("\n[2] Creating test folder...")
    test_path = create_test_folder()
    if not test_path:
        return
    
    # Add scan target
    print("\n[3] Adding scan target...")
    target_id = add_scan_target_via_api(token, test_path)
    
    # Start monitoring  
    print("\n[4] Starting monitoring...")
    if start_monitoring(token):
        
        # Create permission change
        print("\n[5] Creating permission change...")
        if create_permission_change(test_path):
            
            # Check for detected changes
            print("\n[6] Checking for detected changes...")
            check_for_changes_after_test()
    
    print("\n" + "=" * 40)
    print("Test completed!")

if __name__ == "__main__":
    main()