#!/usr/bin/env python3
"""Debug polling and create a real alert"""

import sqlite3
import urllib.request
import json
import time
from datetime import datetime

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

def check_alerts_api(token):
    """Check what the alerts API returns"""
    try:
        # Test the same API call the frontend is making
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/alerts/?acknowledged=false&hours=24&limit=5",
            headers={'Authorization': f'Bearer {token}'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
        print(f"📊 Alerts API response: {len(data)} alerts")
        for alert in data:
            print(f"  Alert ID: {alert.get('id')}, Severity: {alert.get('severity')}")
            print(f"    Message: {alert.get('message')}")
            print(f"    Created: {alert.get('created_at')}")
            print()
        
        return data
        
    except Exception as e:
        print(f"❌ Error checking alerts API: {e}")
        return []

def create_real_alert_in_database():
    """Create a real alert directly in the database"""
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        # First check if alerts table exists and its structure
        cursor.execute("PRAGMA table_info(alerts);")
        columns = cursor.fetchall()
        
        print("📊 Alerts table structure:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Create a test alert configuration first
        cursor.execute("""
            INSERT INTO alert_configurations (name, alert_type, severity, conditions, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Test Alert Config",
            "permission_change", 
            "high",
            '{"test": true}',
            1,
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        ))
        
        config_id = cursor.lastrowid
        print(f"✓ Created alert configuration: {config_id}")
        
        # Create a test alert
        cursor.execute("""
            INSERT INTO alerts (config_id, severity, message, details, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            config_id,
            "high",
            "Test alert for polling system - File permissions changed",
            '{"test": true, "path": "C:\\\\ShareGuardTest", "change_type": "permission_added"}',
            datetime.utcnow().isoformat()
        ))
        
        alert_id = cursor.lastrowid
        print(f"✓ Created test alert: {alert_id}")
        
        conn.commit()
        conn.close()
        
        return alert_id
        
    except Exception as e:
        print(f"❌ Error creating alert in database: {e}")
        return None

def check_database_alerts():
    """Check alerts in database"""
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, config_id, severity, message, created_at, acknowledged_at
            FROM alerts 
            ORDER BY created_at DESC 
            LIMIT 10;
        """)
        
        alerts = cursor.fetchall()
        
        print(f"📊 Database alerts: {len(alerts)}")
        for alert in alerts:
            alert_id, config_id, severity, message, created_at, ack_at = alert
            status = "acknowledged" if ack_at else "unacknowledged"
            print(f"  ID: {alert_id}, Config: {config_id}, Severity: {severity}")
            print(f"    Status: {status}, Created: {created_at}")
            print(f"    Message: {message}")
            print()
        
        conn.close()
        return alerts
        
    except Exception as e:
        print(f"❌ Error checking database alerts: {e}")
        return []

def force_websocket_failure_and_polling():
    """Check WebSocket connection attempts and polling status"""
    print("🔍 Checking WebSocket and polling status...")
    print("\nTo see polling in action:")
    print("1. Open browser console on /alerts page")
    print("2. Look for 'Max reconnection attempts reached' message")
    print("3. Look for API requests to /api/v1/alerts/ every 10 seconds")
    print("4. Check if connectionStatus becomes 'polling'")
    
    print("\nIn the browser console, you should see:")
    print("- WebSocket error: Event {isTrusted: true, type: 'error'}")
    print("- WebSocket connection failed. Will retry...")
    print("- After 3 attempts: 'Max reconnection attempts reached. Falling back to polling mode.'")

def main():
    print("ShareGuard Polling Debug and Alert Creation")
    print("=" * 50)
    
    token = get_auth_token()
    if not token:
        print("❌ No authentication token available")
        return
    
    print("✓ Got authentication token")
    
    # Check current alerts via API
    print("\n[1] Checking current alerts via API...")
    api_alerts = check_alerts_api(token)
    
    # Check database alerts
    print("\n[2] Checking alerts in database...")
    db_alerts = check_database_alerts()
    
    # Create a real alert
    print("\n[3] Creating test alert in database...")
    alert_id = create_real_alert_in_database()
    
    if alert_id:
        # Wait a moment and check API again
        print("\n[4] Checking API again after creating alert...")
        time.sleep(2)
        api_alerts_after = check_alerts_api(token)
        
        if len(api_alerts_after) > len(api_alerts):
            print("🎉 New alert is now visible via API!")
        else:
            print("⚠️ New alert not yet visible via API")
    
    # Explain polling behavior
    print("\n[5] WebSocket and Polling Status...")
    force_websocket_failure_and_polling()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")
    print("\n📋 Next steps:")
    print("1. Refresh the /alerts page in your browser")
    print("2. Wait for WebSocket to fail 3 times")
    print("3. Check if the new alert appears")
    print("4. Look for toast notifications")
    print("\nIf the alert appears after refresh, polling is working!")

if __name__ == "__main__":
    main()