#!/usr/bin/env python3
import sqlite3
from pathlib import Path

def clear_all_alerts():
    """Clear all alerts and permission changes to start fresh"""
    db_path = Path("/mnt/c/ShareGuard/shareguard.db")
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check current counts
        cursor.execute("SELECT COUNT(*) FROM alerts")
        alert_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM permission_changes")
        change_count = cursor.fetchone()[0]
        
        print(f"Current status:")
        print(f"  - Alerts: {alert_count}")
        print(f"  - Permission changes: {change_count}")
        
        # Clear all alerts
        cursor.execute("DELETE FROM alerts")
        alerts_deleted = cursor.rowcount
        
        # Clear all permission changes
        cursor.execute("DELETE FROM permission_changes")
        changes_deleted = cursor.rowcount
        
        # Reset auto-increment counters (if table exists)
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='alerts'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='permission_changes'")
        except sqlite3.OperationalError:
            # sqlite_sequence table doesn't exist, which is fine
            pass
        
        conn.commit()
        
        print(f"\n✅ Successfully cleared:")
        print(f"  - {alerts_deleted} alerts deleted")
        print(f"  - {changes_deleted} permission changes deleted")
        print(f"  - Auto-increment counters reset")
        
        # Verify cleanup
        cursor.execute("SELECT COUNT(*) FROM alerts")
        remaining_alerts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM permission_changes")
        remaining_changes = cursor.fetchone()[0]
        
        print(f"\n📊 After cleanup:")
        print(f"  - Alerts: {remaining_alerts}")
        print(f"  - Permission changes: {remaining_changes}")
        
        print(f"\n🎉 Database is now clean and ready for new alerts!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧹 ShareGuard Alert Database Cleanup")
    print("=" * 40)
    
    response = input("\nThis will delete ALL alerts and permission changes. Continue? (y/N): ")
    if response.lower() == 'y':
        clear_all_alerts()
    else:
        print("Operation cancelled.")