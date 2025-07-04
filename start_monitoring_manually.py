#!/usr/bin/env python3
import os
import sys
import sqlite3
from pathlib import Path

def start_monitoring_manually():
    """Start monitoring manually with scan target paths"""
    db_path = Path("/mnt/c/ShareGuard/shareguard.db")
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all scan targets
        cursor.execute("SELECT id, name, path FROM scan_targets")
        targets = cursor.fetchall()
        
        existing_paths = []
        for target in targets:
            target_id, name, path = target
            if path and os.path.exists(path):
                existing_paths.append(path)
                print(f"✓ Found existing path: {path} ({name})")
            else:
                print(f"✗ Path does not exist: {path} ({name})")
        
        print(f"\nFound {len(existing_paths)} existing paths to monitor:")
        for path in existing_paths:
            print(f"  - {path}")
        
        # Here we would normally call the monitoring service
        # but since we don't have the backend running, we'll just show what should be monitored
        print(f"\nThe monitoring service should be started with these {len(existing_paths)} paths")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_monitoring_manually()