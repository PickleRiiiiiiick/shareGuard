#!/usr/bin/env python3
import os
import sys
import sqlite3
from pathlib import Path

def check_scan_targets():
    """Check scan targets in the database"""
    db_path = Path("/mnt/c/ShareGuard/shareguard.db")
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if scan targets table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='scan_targets'
        """)
        if not cursor.fetchone():
            print("scan_targets table does not exist")
            return
        
        # Get table schema
        cursor.execute("PRAGMA table_info(scan_targets)")
        columns = cursor.fetchall()
        print("Table structure:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Get all scan targets
        cursor.execute("SELECT * FROM scan_targets")
        targets = cursor.fetchall()
        
        print(f"\nFound {len(targets)} scan targets:")
        for target in targets:
            print(f"  {target}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking scan targets: {e}")

if __name__ == "__main__":
    check_scan_targets()