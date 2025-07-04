#!/usr/bin/env python3
"""Test polling notifications with new alerts"""

import sqlite3
import time
from datetime import datetime

def create_new_alert_for_polling_test():
    """Create a new alert to test polling detection"""
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        # Create a critical alert to test notifications
        cursor.execute("""
            INSERT INTO alerts (config_id, severity, message, details, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            2,  # Use the existing config we created
            "critical",
            "🚨 CRITICAL: Unauthorized access detected on ShareGuard system",
            '{"test": true, "path": "C:\\\\ShareGuardTest", "change_type": "permission_modified", "user": "Unknown"}',
            datetime.utcnow().isoformat()
        ))
        
        alert_id = cursor.lastrowid
        print(f"✓ Created CRITICAL alert: {alert_id}")
        
        # Wait a moment then create a medium alert
        time.sleep(2)
        
        cursor.execute("""
            INSERT INTO alerts (config_id, severity, message, details, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            2,
            "medium",
            "📝 INFO: New user access granted to Finance folder",
            '{"test": true, "path": "C:\\\\ShareGuardTest\\\\Finance", "change_type": "permission_added", "user": "john.doe"}',
            datetime.utcnow().isoformat()
        ))
        
        alert_id2 = cursor.lastrowid
        print(f"✓ Created MEDIUM alert: {alert_id2}")
        
        conn.commit()
        conn.close()
        
        return [alert_id, alert_id2]
        
    except Exception as e:
        print(f"❌ Error creating alerts: {e}")
        return []

def check_latest_alerts():
    """Check the latest alerts in database"""
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, severity, message, created_at
            FROM alerts 
            ORDER BY created_at DESC 
            LIMIT 5;
        """)
        
        alerts = cursor.fetchall()
        
        print(f"📊 Latest alerts in database:")
        for alert in alerts:
            alert_id, severity, message, created_at = alert
            print(f"  ID: {alert_id}, Severity: {severity}")
            print(f"    Message: {message}")
            print(f"    Created: {created_at}")
            print()
        
        conn.close()
        return alerts
        
    except Exception as e:
        print(f"❌ Error checking alerts: {e}")
        return []

def main():
    print("ShareGuard Polling Notifications Test")
    print("=" * 40)
    
    print("[1] Current alerts in database:")
    current_alerts = check_latest_alerts()
    
    print("\n[2] Creating new alerts for polling test...")
    new_alert_ids = create_new_alert_for_polling_test()
    
    if new_alert_ids:
        print("\n[3] Latest alerts after creation:")
        check_latest_alerts()
        
        print("\n🔔 POLLING TEST INSTRUCTIONS:")
        print("=" * 40)
        print("1. Keep your browser open on the /alerts page")
        print("2. Watch the browser console for:")
        print("   - API requests every 10 seconds")
        print("   - 'Max reconnection attempts reached. Falling back to polling mode.'")
        print("3. Within 10 seconds, you should see:")
        print("   - 🚨 CRITICAL toast notification (red)")
        print("   - 📝 INFO toast notification (blue)")
        print("   - Notification count increase")
        print("   - Alerts appear in the notifications bell")
        print("4. Check the alerts dashboard for updated count")
        print("\n⏰ The polling happens every 10 seconds.")
        print("If WebSocket failed 3 times, polling should be active now.")
        print("\n✅ If you see the toast notifications, polling is working!")
        
    print("\n" + "=" * 40)
    print("Test completed!")

if __name__ == "__main__":
    main()