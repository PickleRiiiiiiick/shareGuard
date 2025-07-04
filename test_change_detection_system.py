#!/usr/bin/env python3
import os
import sys
import sqlite3
from pathlib import Path
import time
import json
from datetime import datetime

def test_change_detection_system():
    """Test the change detection system end-to-end"""
    db_path = Path("/mnt/c/ShareGuard/shareguard.db")
    test_path = "C:\\ShareGuardTest"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    if not os.path.exists(test_path):
        print(f"Test path does not exist: {test_path}")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("=== Change Detection System Test ===\n")
        
        # 1. Check current cache entries
        print("1. Checking current cache entries...")
        cursor.execute("SELECT COUNT(*) FROM folder_permission_cache WHERE folder_path = ?", (test_path,))
        cache_count = cursor.fetchone()[0]
        print(f"   Cache entries for {test_path}: {cache_count}")
        
        # 2. Check current alerts
        print("\n2. Checking current alerts...")
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE created_at > datetime('now', '-1 hour')")
        recent_alerts = cursor.fetchone()[0]
        print(f"   Recent alerts (last hour): {recent_alerts}")
        
        # 3. Check permission changes
        print("\n3. Checking permission changes...")
        cursor.execute("SELECT COUNT(*) FROM permission_changes WHERE detected_time > datetime('now', '-1 hour')")
        recent_changes = cursor.fetchone()[0]
        print(f"   Recent permission changes (last hour): {recent_changes}")
        
        # 4. Check if monitoring is configured
        print("\n4. Checking monitoring configuration...")
        cursor.execute("SELECT id, name, path FROM scan_targets WHERE path = ?", (test_path,))
        target = cursor.fetchone()
        if target:
            print(f"   ✓ Scan target found: {target[1]} (ID: {target[0]})")
        else:
            print(f"   ✗ No scan target found for {test_path}")
        
        # 5. Create a test alert to verify the notification system
        print("\n5. Creating test alert...")
        test_alert = {
            "severity": "info",
            "message": f"🔧 TEST: Change detection system test for {test_path}",
            "details": json.dumps({
                "path": test_path,
                "test": True,
                "alert_type": "change_detection_test",
                "timestamp": datetime.utcnow().isoformat()
            }),
            "created_at": datetime.utcnow().isoformat()
        }
        
        cursor.execute("""
            INSERT INTO alerts (severity, message, details, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            test_alert["severity"],
            test_alert["message"],
            test_alert["details"],
            test_alert["created_at"]
        ))
        
        alert_id = cursor.lastrowid
        conn.commit()
        
        print(f"   ✓ Test alert created with ID: {alert_id}")
        
        # 6. Summary
        print("\n6. System Status Summary:")
        print(f"   • Monitoring path: {test_path}")
        print(f"   • Path exists: {os.path.exists(test_path)}")
        print(f"   • Scan target configured: {'Yes' if target else 'No'}")
        print(f"   • Cache entries: {cache_count}")
        print(f"   • Recent alerts: {recent_alerts + 1}")  # +1 for the one we just created
        print(f"   • Recent changes: {recent_changes}")
        
        # 7. Next steps
        print("\n7. Next Steps:")
        print("   • Backend should auto-detect the scan target path on startup")
        print("   • Monitoring should start automatically")
        print("   • Any ACL changes to C:\\ShareGuardTest should be detected")
        print("   • Alerts should appear in the UI and trigger notifications")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_change_detection_system()