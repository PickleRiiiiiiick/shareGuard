#!/usr/bin/env python3
"""Test the complete change detection pipeline"""

import sqlite3
import time
import os
import json
from datetime import datetime

def check_database_changes():
    """Check the database for permission changes"""
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        # Check permission_changes table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='permission_changes';
        """)
        
        if not cursor.fetchone():
            print("⚠️ permission_changes table not found")
            return
        
        # Get recent permission changes
        cursor.execute("""
            SELECT id, scan_job_id, change_type, detected_time, 
                   previous_state, current_state
            FROM permission_changes 
            ORDER BY detected_time DESC 
            LIMIT 10;
        """)
        
        changes = cursor.fetchall()
        
        if not changes:
            print("📝 No permission changes found in database")
        else:
            print(f"📝 Found {len(changes)} recent permission changes:")
            for change in changes[:3]:  # Show last 3
                change_id, job_id, change_type, detected_time, prev_state, curr_state = change
                print(f"  ID: {change_id}, Type: {change_type}, Time: {detected_time}")
                if prev_state:
                    try:
                        prev = json.loads(prev_state)
                        print(f"    Previous: {prev.get('path', 'N/A')}")
                    except:
                        pass
                if curr_state:
                    try:
                        curr = json.loads(curr_state)
                        print(f"    Current: {curr.get('path', 'N/A')}")
                    except:
                        pass
                print()
        
        # Check alerts table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='alerts';
        """)
        
        if cursor.fetchone():
            cursor.execute("""
                SELECT id, severity, message, created_at, acknowledged_at
                FROM alerts 
                ORDER BY created_at DESC 
                LIMIT 5;
            """)
            
            alerts = cursor.fetchall()
            
            if not alerts:
                print("🔔 No alerts found in database")
            else:
                print(f"🔔 Found {len(alerts)} recent alerts:")
                for alert in alerts[:3]:  # Show last 3
                    alert_id, severity, message, created_at, ack_at = alert
                    status = "acknowledged" if ack_at else "unacknowledged"
                    print(f"  ID: {alert_id}, Severity: {severity}, Status: {status}")
                    print(f"    Message: {message}")
                    print(f"    Time: {created_at}")
                    print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def check_monitoring_status():
    """Check if monitoring is active"""
    try:
        import urllib.request
        import json
        
        # Get auth token from a recent successful login
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
        
        if not result:
            print("⚠️ No active session found - cannot check monitoring status")
            return
        
        token = result[0]
        
        # Check monitoring status
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
        print(f"    Queue size: {stats.get('queue_size', 0)}")
        
    except Exception as e:
        print(f"❌ Error checking monitoring status: {e}")

def check_scan_targets():
    """Check what scan targets are configured"""
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, path, is_active, last_scan_id
            FROM scan_targets 
            WHERE is_active = 1
            ORDER BY created_at DESC;
        """)
        
        targets = cursor.fetchall()
        
        if not targets:
            print("⚠️ No active scan targets found")
        else:
            print(f"🎯 Found {len(targets)} active scan targets:")
            for target in targets:
                target_id, name, path, is_active, last_scan = target
                print(f"  ID: {target_id}, Name: {name}")
                print(f"    Path: {path}")
                print(f"    Last scan: {last_scan}")
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking scan targets: {e}")

def suggest_test_folder():
    """Suggest creating a test folder for permission changes"""
    test_path = "C:\\ShareGuardTest"
    
    print(f"\n💡 To test change detection:")
    print(f"1. Create folder: {test_path}")
    print(f"2. Add it as a scan target in the UI")
    print(f"3. Start monitoring")
    print(f"4. Change permissions on the folder")
    print(f"5. Check logs and database for detected changes")
    
    if os.path.exists(test_path):
        print(f"✓ Test folder already exists: {test_path}")
    else:
        print(f"⚠️ Test folder does not exist: {test_path}")

def main():
    print("ShareGuard Change Detection Pipeline Test")
    print("=" * 50)
    
    print("\n[1] Checking database for recent changes...")
    check_database_changes()
    
    print("\n[2] Checking monitoring status...")
    check_monitoring_status()
    
    print("\n[3] Checking scan targets...")
    check_scan_targets()
    
    suggest_test_folder()
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main()