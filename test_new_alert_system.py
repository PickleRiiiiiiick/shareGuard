#!/usr/bin/env python3
import sqlite3
import time
from pathlib import Path
from datetime import datetime

def test_new_alert_system():
    """Test the new alert system with user-friendly formatting"""
    db_path = Path("/mnt/c/ShareGuard/shareguard.db")
    
    print("🧪 Testing New Alert System")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 1. Check current alert count
        cursor.execute("SELECT COUNT(*) FROM alerts")
        alert_count = cursor.fetchone()[0]
        print(f"📊 Current alerts in database: {alert_count}")
        
        # 2. Create a test alert with the new format
        print(f"\n📝 Creating test alert with new user-friendly format...")
        
        new_alert_details = {
            "folder": {
                "name": "Finance",
                "full_path": "C:\\ShareGuardTest\\Finance"
            },
            "summary": {
                "changes_detected": 2,
                "severity_level": "high"
            },
            "changes": [
                {
                    "type": "Permissions Added",
                    "icon": "➕",
                    "description": "2 new permissions granted",
                    "users_affected": ["john.doe", "finance_team"],
                    "impact": "Medium - New users/groups can access this folder"
                },
                {
                    "type": "Owner Change",
                    "icon": "🔄",
                    "description": "Folder owner changed from 'SYSTEM' to 'finance_admin'",
                    "impact": "High - Ownership changes can affect access control"
                }
            ],
            "metadata": {
                "detected_at": datetime.utcnow().isoformat(),
                "source": "Real-time Monitoring",
                "alert_type": "Permission Change"
            }
        }
        
        import json
        cursor.execute("""
            INSERT INTO alerts (severity, message, details, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            "high",
            "📁 Finance: ➕ 2 permissions added, 🔄 Owner changed",
            json.dumps(new_alert_details),
            datetime.utcnow().isoformat()
        ))
        
        test_alert_id = cursor.lastrowid
        conn.commit()
        
        print(f"   ✅ Test alert created (ID: {test_alert_id})")
        
        # 3. Verify the alert was created correctly
        cursor.execute("""
            SELECT id, severity, message, details, created_at 
            FROM alerts 
            WHERE id = ?
        """, (test_alert_id,))
        
        alert = cursor.fetchone()
        if alert:
            alert_id, severity, message, details, created_at = alert
            print(f"\n📋 Alert Details:")
            print(f"   ID: {alert_id}")
            print(f"   Severity: {severity}")
            print(f"   Message: {message}")
            print(f"   Created: {created_at}")
            
            # Parse and display the structured details
            try:
                details_obj = json.loads(details)
                print(f"\n🔍 Structured Details:")
                print(f"   Folder: {details_obj['folder']['name']}")
                print(f"   Changes: {details_obj['summary']['changes_detected']}")
                print(f"   Severity: {details_obj['summary']['severity_level']}")
                
                for i, change in enumerate(details_obj['changes'], 1):
                    print(f"   Change {i}: {change['icon']} {change['type']} - {change['description']}")
                    
            except Exception as e:
                print(f"   ❌ Error parsing details: {e}")
        
        # 4. Check total alerts now
        cursor.execute("SELECT COUNT(*) FROM alerts")
        new_alert_count = cursor.fetchone()[0]
        print(f"\n📊 Total alerts after test: {new_alert_count}")
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Check the alerts page in the UI")
        print(f"   2. The new alert should have a 'NEW' badge and blue highlight")
        print(f"   3. Click 'expand details' to see the beautiful new format")
        print(f"   4. Make a real ACL change to test live detection")
        
        print(f"\n✅ New alert system test completed successfully!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_alert_system()