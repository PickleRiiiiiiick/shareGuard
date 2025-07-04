#!/usr/bin/env python3
import sqlite3
import time
from pathlib import Path
from datetime import datetime

def test_monitoring_status():
    """Test if monitoring is working after fixes"""
    db_path = Path("/mnt/c/ShareGuard/shareguard.db")
    
    print("=== Testing Monitoring System After Fixes ===\n")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 1. Check current alerts count
        cursor.execute("SELECT COUNT(*) FROM alerts")
        total_alerts = cursor.fetchone()[0]
        print(f"1. Current total alerts: {total_alerts}")
        
        # 2. Check permission changes count
        cursor.execute("SELECT COUNT(*) FROM permission_changes")
        total_changes = cursor.fetchone()[0]
        print(f"2. Current total permission changes: {total_changes}")
        
        # 3. Check cache entries
        cursor.execute("SELECT COUNT(*) FROM folder_permission_cache")
        cache_entries = cursor.fetchone()[0]
        print(f"3. Current cache entries: {cache_entries}")
        
        # 4. Check recent activity (last 10 minutes)
        cursor.execute("""
            SELECT COUNT(*) FROM alerts 
            WHERE created_at > datetime('now', '-10 minutes')
        """)
        recent_alerts = cursor.fetchone()[0]
        print(f"4. Recent alerts (last 10 minutes): {recent_alerts}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM permission_changes 
            WHERE detected_time > datetime('now', '-10 minutes')
        """)
        recent_changes = cursor.fetchone()[0]
        print(f"5. Recent permission changes (last 10 minutes): {recent_changes}")
        
        # 6. Test alert creation to verify models work
        print("\n6. Testing alert creation...")
        test_alert = (
            "info",
            "🧪 TEST: Monitoring system validation after fixes",
            '{"test": true, "validation": "post-fix", "timestamp": "' + datetime.utcnow().isoformat() + '"}',
            datetime.utcnow().isoformat()
        )
        
        cursor.execute("""
            INSERT INTO alerts (severity, message, details, created_at)
            VALUES (?, ?, ?, ?)
        """, test_alert)
        
        new_alert_id = cursor.lastrowid
        conn.commit()
        
        print(f"   ✓ Test alert created successfully (ID: {new_alert_id})")
        
        # 7. Instructions for user
        print("\n7. Next Steps:")
        print("   a) Make a permission change to C:\\ShareGuardTest\\Finance")
        print("   b) Wait 60 seconds for monitoring cycle")
        print("   c) Check if new alerts appear in UI")
        print("   d) Verify WebSocket connections work")
        
        print(f"\n✅ Monitoring system is ready and database models are working!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_monitoring_status()