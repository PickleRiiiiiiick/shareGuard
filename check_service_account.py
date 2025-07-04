#!/usr/bin/env python3
"""Check service account in database"""

import sqlite3
import hashlib
import sys

def check_service_account():
    """Check service account configuration"""
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        # Check if service_accounts table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='service_accounts';
        """)
        
        if not cursor.fetchone():
            print("service_accounts table not found")
            return
        
        # Get service account info
        cursor.execute("SELECT * FROM service_accounts")
        accounts = cursor.fetchall()
        
        if not accounts:
            print("No service accounts found in database")
            return
        
        # Get column names
        cursor.execute("PRAGMA table_info(service_accounts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print("Service Accounts:")
        print("-" * 50)
        
        for account in accounts:
            print(f"Account ID: {account[0]}")
            for i, value in enumerate(account[1:], 1):
                if columns[i] == 'password_hash':
                    print(f"  {columns[i]}: {value[:20]}..." if value else f"  {columns[i]}: None")
                else:
                    print(f"  {columns[i]}: {value}")
            print()
        
        # Test password hash
        print("Testing password verification:")
        test_passwords = [
            "ShareGuardService",
            "P@ssw0rd123!",
            "password",
            "admin"
        ]
        
        for account in accounts:
            stored_hash = account[columns.index('password_hash')]
            print(f"\nAccount: {account[columns.index('username')]}")
            
            for test_pw in test_passwords:
                # Try different hash methods
                hashes = [
                    hashlib.sha256(test_pw.encode()).hexdigest(),
                    hashlib.md5(test_pw.encode()).hexdigest(),
                    test_pw  # Plain text
                ]
                
                for hash_method, hash_value in zip(['SHA256', 'MD5', 'Plain'], hashes):
                    if stored_hash == hash_value:
                        print(f"  ✓ Password '{test_pw}' matches ({hash_method})")
                        break
                else:
                    print(f"  ✗ Password '{test_pw}' does not match")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_service_account()