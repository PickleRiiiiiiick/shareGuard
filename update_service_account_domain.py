#!/usr/bin/env python3
"""
Update ShareGuardService account domain to match Windows authentication
"""
import sqlite3
import json
from datetime import datetime
import socket

def main():
    # Get the Windows computer name which acts as the domain for local accounts
    computer_name = socket.gethostname()
    print(f"Detected computer name: {computer_name}")
    
    # Connect to the database
    conn = sqlite3.connect('shareguard.db')
    cursor = conn.cursor()
    
    # Check current service account details
    cursor.execute("""
        SELECT id, username, domain, permissions, is_active 
        FROM service_accounts 
        WHERE username = 'ShareGuardService'
    """)
    
    result = cursor.fetchone()
    if not result:
        print("ERROR: ShareGuardService account not found!")
        conn.close()
        return
    
    id, username, current_domain, permissions, is_active = result
    print(f"\nCurrent ShareGuardService account:")
    print(f"  ID: {id}")
    print(f"  Username: {username}")
    print(f"  Current Domain: {current_domain}")
    print(f"  Is Active: {is_active}")
    
    # Update the domain to the computer name
    print(f"\nUpdating domain from '{current_domain}' to '{computer_name}'...")
    
    cursor.execute("""
        UPDATE service_accounts 
        SET domain = ?,
            updated_at = ?
        WHERE id = ?
    """, (computer_name, datetime.utcnow().isoformat(), id))
    
    # Commit changes
    conn.commit()
    
    # Verify the update
    cursor.execute("""
        SELECT id, username, domain, permissions, is_active 
        FROM service_accounts 
        WHERE id = ?
    """, (id,))
    
    result = cursor.fetchone()
    if result:
        id, username, domain, permissions, is_active = result
        perms_list = json.loads(permissions)
        
        print("\nUpdated ShareGuardService account details:")
        print(f"  ID: {id}")
        print(f"  Username: {username}")
        print(f"  Domain: {domain}")
        print(f"  Is Active: {is_active}")
        print(f"  Permissions ({len(perms_list)}):")
        for perm in sorted(perms_list):
            print(f"    - {perm}")
    
    conn.close()
    print(f"\nShareGuardService account domain has been updated to '{computer_name}'!")
    print("\nNOTE: You should now login using:")
    print(f"  Username: ShareGuardService")
    print(f"  Domain: {computer_name}")
    print(f"  Password: <your Windows password for ShareGuardService>")

if __name__ == "__main__":
    main()