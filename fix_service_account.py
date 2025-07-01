#!/usr/bin/env python3
"""
Fix ShareGuardService account permissions
"""
import sqlite3
import json
from datetime import datetime

# All permissions required by the application
ALL_PERMISSIONS = [
    "scan:execute",
    "scan:read", 
    "scan:admin",
    "folders:read",
    "folders:validate",
    "folders:modify",
    "cache:clear",
    "cache:read",
    "targets:read",
    "targets:write",
    "targets:create",
    "targets:delete",
    "users:read",
    "users:write",
    "health:read",
    "health:write"
]

def main():
    # Connect to the database
    conn = sqlite3.connect('shareguard.db')
    cursor = conn.cursor()
    
    # Check if ShareGuardService exists
    cursor.execute("""
        SELECT id FROM service_accounts 
        WHERE username = 'ShareGuardService'
    """)
    existing = cursor.fetchone()
    
    if existing:
        # Update existing account
        account_id = existing[0]
        print(f"Updating existing ShareGuardService account (ID: {account_id})")
        
        cursor.execute("""
            UPDATE service_accounts 
            SET permissions = ?,
                is_active = 1,
                updated_at = ?
            WHERE id = ?
        """, (json.dumps(ALL_PERMISSIONS), datetime.utcnow().isoformat(), account_id))
        
    else:
        # Create new account
        print("Creating new ShareGuardService account")
        
        cursor.execute("""
            INSERT INTO service_accounts (username, domain, description, permissions, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'ShareGuardService',
            'SYSTEM',
            'ShareGuard Service Account with full permissions',
            json.dumps(ALL_PERMISSIONS),
            1,
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        ))
        
        account_id = cursor.lastrowid
    
    # Commit changes
    conn.commit()
    
    # Verify the account
    cursor.execute("""
        SELECT id, username, domain, permissions, is_active 
        FROM service_accounts 
        WHERE id = ?
    """, (account_id,))
    
    result = cursor.fetchone()
    if result:
        id, username, domain, permissions, is_active = result
        perms_list = json.loads(permissions)
        
        print("\nShareGuardService account details:")
        print(f"  ID: {id}")
        print(f"  Username: {username}")
        print(f"  Domain: {domain}")
        print(f"  Is Active: {is_active}")
        print(f"  Permissions ({len(perms_list)}):")
        for perm in sorted(perms_list):
            print(f"    - {perm}")
    
    conn.close()
    print("\nShareGuardService account has been fixed!")

if __name__ == "__main__":
    main()