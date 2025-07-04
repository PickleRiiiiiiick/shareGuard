#!/usr/bin/env python3
import sqlite3
from pathlib import Path

def check_alerts_table():
    """Check alerts table structure"""
    db_path = Path("/mnt/c/ShareGuard/shareguard.db")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(alerts)")
        columns = cursor.fetchall()
        print("Alerts table structure:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check recent alerts
        cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 3")
        alerts = cursor.fetchall()
        print(f"\nRecent alerts:")
        for alert in alerts:
            print(f"  {alert}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_alerts_table()