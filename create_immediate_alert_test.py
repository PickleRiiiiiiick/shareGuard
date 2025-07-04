#!/usr/bin/env python3
"""Create an immediate alert to test toast notifications"""

import sqlite3
from datetime import datetime

def create_immediate_alert():
    """Create a new alert to test if toast notifications work"""
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        # Create a new critical alert with current timestamp
        cursor.execute("""
            INSERT INTO alerts (config_id, severity, message, details, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            2,  # Use existing config
            "critical",
            "🔥 URGENT: Security breach detected - Immediate action required!",
            '{"test": true, "alert_type": "security_breach", "location": "ShareGuard System"}',
            datetime.utcnow().isoformat()
        ))
        
        alert_id = cursor.lastrowid
        print(f"✓ Created new CRITICAL alert: {alert_id}")
        print(f"  Message: 🔥 URGENT: Security breach detected - Immediate action required!")
        print(f"  Time: {datetime.utcnow().isoformat()}")
        
        conn.commit()
        conn.close()
        
        print("\n🔔 NOTIFICATION TEST:")
        print("=" * 30)
        print("1. Keep your browser open on /alerts page")
        print("2. Within 10 seconds, you should see:")
        print("   - 🔥 Red toast notification")
        print("   - Alert count increase")
        print("   - New alert in notifications bell")
        print("3. If you see the toast, polling notifications are working!")
        
        return alert_id
        
    except Exception as e:
        print(f"❌ Error creating alert: {e}")
        return None

def check_total_alerts():
    """Check total alerts in database"""
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM alerts;")
        total = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT id, severity, message, created_at
            FROM alerts 
            ORDER BY created_at DESC 
            LIMIT 3;
        """)
        
        recent = cursor.fetchall()
        
        print(f"📊 Total alerts: {total}")
        print("Recent alerts:")
        for alert in recent:
            alert_id, severity, message, created_at = alert
            print(f"  ID: {alert_id}, {severity}: {message[:50]}...")
        
        conn.close()
        return total
        
    except Exception as e:
        print(f"❌ Error checking alerts: {e}")
        return 0

def main():
    print("ShareGuard Immediate Alert Test")
    print("=" * 35)
    
    print("[1] Current alerts:")
    current_total = check_total_alerts()
    
    print(f"\n[2] Creating new alert (current total: {current_total})...")
    alert_id = create_immediate_alert()
    
    if alert_id:
        print(f"\n[3] Alert created successfully!")
        print("✅ The polling system should detect this within 10 seconds")
        print("✅ Look for a red toast notification in your browser")
        print("✅ Check the notification bell for the new alert")
        
        print(f"\n🎯 Expected behavior:")
        print(f"   - Total alerts should increase to {current_total + 1}")
        print(f"   - Toast: '🔥 URGENT: Security breach detected...'")
        print(f"   - Notification badge should update")
        
    print("\n" + "=" * 35)
    print("⏰ Watch your browser for the next 10 seconds!")

if __name__ == "__main__":
    main()