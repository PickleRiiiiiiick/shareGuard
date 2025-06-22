#!/usr/bin/env python3
"""
Debug script to test SID resolution functionality.
Run this script to test the enhanced SID resolution methods.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.scanner.file_scanner import PermissionScanner
    import win32security
    import logging
    
    # Configure logging to see debug messages
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
    
    def test_sid_resolution():
        print("Testing SID Resolution...")
        print("=" * 50)
        
        scanner = PermissionScanner()
        
        # Test with some well-known SIDs
        test_sids = [
            "S-1-1-0",  # Everyone
            "S-1-5-32-544",  # Administrators
            "S-1-5-32-545",  # Users
            "S-1-5-18",  # SYSTEM
            "S-1-5-21-1923339626-2680576837-3225702567-500",  # Domain Administrator (example)
            "S-1-5-21-1923339626-2680576837-3225702567-512",  # Domain Admins (example)
        ]
        
        for sid_string in test_sids:
            print(f"\nTesting SID: {sid_string}")
            try:
                # Convert string SID to binary
                sid_binary = win32security.ConvertStringSidToSid(sid_string)
                
                # Test resolution
                result = scanner._get_trustee_name(sid_binary)
                
                print(f"  Result: {result}")
                print(f"  Name: {result.get('name', 'N/A')}")
                print(f"  Domain: {result.get('domain', 'N/A')}")
                print(f"  Full Name: {result.get('full_name', 'N/A')}")
                print(f"  Account Type: {result.get('account_type', 'N/A')}")
                
            except Exception as e:
                print(f"  Error: {str(e)}")
        
        # Print cache stats
        print(f"\nSID Cache Stats:")
        stats = scanner.get_sid_cache_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
        return scanner
        
    def test_real_folder(folder_path):
        """Test SID resolution on a real folder."""
        print(f"\nTesting real folder: {folder_path}")
        print("=" * 50)
        
        scanner = PermissionScanner()
        
        try:
            result = scanner.get_folder_permissions(folder_path)
            
            if result.get('success'):
                aces = result.get('aces', [])
                print(f"Found {len(aces)} ACEs:")
                
                for i, ace in enumerate(aces):
                    trustee = ace.get('trustee', {})
                    print(f"\nACE {i+1}:")
                    print(f"  SID: {trustee.get('sid', 'N/A')}")
                    print(f"  Name: {trustee.get('name', 'N/A')}")
                    print(f"  Domain: {trustee.get('domain', 'N/A')}")
                    print(f"  Full Name: {trustee.get('full_name', 'N/A')}")
                    print(f"  Account Type: {trustee.get('account_type', 'N/A')}")
                    print(f"  Type: {ace.get('type', 'N/A')}")
                    print(f"  Inherited: {ace.get('inherited', 'N/A')}")
            else:
                print(f"Failed to get folder permissions: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Error testing folder: {str(e)}")
    
    if __name__ == "__main__":
        # Test basic SID resolution
        scanner = test_sid_resolution()
        
        # Test with a real folder if provided
        if len(sys.argv) > 1:
            test_folder = sys.argv[1]
            if os.path.exists(test_folder):
                test_real_folder(test_folder)
            else:
                print(f"\nFolder not found: {test_folder}")
        else:
            # Test with current directory
            test_real_folder(".")
            
except ImportError as e:
    print(f"Import error (this script requires Windows and pywin32): {str(e)}")
except Exception as e:
    print(f"Error: {str(e)}")