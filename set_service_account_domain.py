#!/usr/bin/env python3
"""
Set ShareGuardService account domain to shareguard.com
"""
import sqlite3
import json
from datetime import datetime

def main():
    target_domain = "shareguard.com"
    
    # Connect to the database
    conn = sqlite3.connect('shareguard.db')
    cursor = conn.cursor()
    
    # Update the domain
    cursor.execute("""
        UPDATE service_accounts 
        SET domain = ?,
            updated_at = ?
        WHERE username = 'ShareGuardService'
    """, (target_domain, datetime.utcnow().isoformat()))
    
    # Commit changes
    conn.commit()
    
    # Verify the update
    cursor.execute("""
        SELECT id, username, domain, permissions, is_active 
        FROM service_accounts 
        WHERE username = 'ShareGuardService'
    """)
    
    result = cursor.fetchone()
    if result:
        id, username, domain, permissions, is_active = result
        perms_list = json.loads(permissions)
        
        print(f"ShareGuardService account updated:")
        print(f"  Username: {username}")
        print(f"  Domain: {domain}")
        print(f"  Is Active: {is_active}")
        print(f"  Permissions: {len(perms_list)}")
    
    conn.close()
    print(f"\nService account domain has been set to '{target_domain}'")

if __name__ == "__main__":
    main()