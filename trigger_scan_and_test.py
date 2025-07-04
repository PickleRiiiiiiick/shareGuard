#!/usr/bin/env python3
"""Trigger a scan and test change detection"""

import sqlite3
import urllib.request
import json
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

def trigger_scan_on_target(token, target_id):
    """Trigger a scan on a specific target"""
    try:
        data = {
            "target_id": target_id,
            "scan_type": "permission_scan"
        }
        
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/scan/start",
            data=json.dumps(data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            
        print(f"✓ Scan started: {result}")
        return result.get('job_id')
        
    except Exception as e:
        print(f"❌ Error starting scan: {e}")
        return None

def check_recent_scans():
    """Check for recent scan jobs"""
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, target_id, status, started_at, completed_at, 
                   total_files, total_folders, errors_count
            FROM scan_jobs 
            WHERE started_at > datetime('now', '-1 hour')
            ORDER BY started_at DESC
            LIMIT 5;
        """)
        
        scans = cursor.fetchall()
        
        if scans:
            print(f"📊 Found {len(scans)} recent scans:")
            for scan in scans:
                job_id, target_id, status, started, completed, files, folders, errors = scan
                print(f"  Job ID: {job_id}, Target: {target_id}, Status: {status}")
                print(f"    Started: {started}, Completed: {completed}")
                print(f"    Files: {files}, Folders: {folders}, Errors: {errors}")
                print()
        else:
            print("📊 No recent scans found")
        
        conn.close()
        return scans
        
    except Exception as e:
        print(f"❌ Error checking scans: {e}")
        return []

def start_monitoring_with_paths(token):
    """Start monitoring with specific paths"""
    try:
        # Get scan target paths from database
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, path FROM scan_targets LIMIT 5;")
        targets = cursor.fetchall()
        conn.close()
        
        if not targets:
            print("⚠️ No scan targets found")
            return False
        
        paths = [target[1] for target in targets if target[1]]
        print(f"📁 Found paths to monitor: {paths}")
        
        # Start monitoring with specific paths
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
            
        print(f"✓ Started monitoring with paths: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Error starting monitoring with paths: {e}")
        return False

def create_test_alert():
    """Create a test alert via API"""
    try:
        token = get_auth_token()
        
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/alerts/test-notification",
            data=json.dumps({"message": "Test alert from change detection pipeline"}).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            
        print(f"✓ Test notification sent: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending test notification: {e}")
        return False

def main():
    print("ShareGuard Scan and Change Detection Test")
    print("=" * 45)
    
    token = get_auth_token()
    if not token:
        print("❌ No authentication token available")
        return
    
    print("✓ Got authentication token")
    
    # Check recent scans
    print("\n[1] Checking recent scans...")
    recent_scans = check_recent_scans()
    
    # Start monitoring with paths
    print("\n[2] Starting monitoring with specific paths...")
    monitoring_started = start_monitoring_with_paths(token)
    
    # Trigger scan on first target
    print("\n[3] Triggering scan on target...")
    conn = sqlite3.connect('shareguard.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM scan_targets LIMIT 1;")
    target = cursor.fetchone()
    conn.close()
    
    if target:
        target_id = target[0]
        job_id = trigger_scan_on_target(token, target_id)
        
        if job_id:
            print(f"⏳ Waiting for scan to complete...")
            time.sleep(10)
            
            # Check scan status
            print("\n[4] Checking scan results...")
            check_recent_scans()
    
    # Create test notification
    print("\n[5] Creating test notification...")
    create_test_alert()
    
    print("\n" + "=" * 45)
    print("Test completed!")
    print("\nNow check your browser alerts page to see if:")
    print("1. The test notification appears")
    print("2. The polling fallback is working")
    print("3. Toast notifications show up")

if __name__ == "__main__":
    main()