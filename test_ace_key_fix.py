#!/usr/bin/env python3
"""Test script to verify the ACE key fix is working correctly."""

import sys
import os
sys.path.insert(0, '/mnt/c/ShareGuard/src')

from services.change_monitor import ChangeMonitorService

def test_ace_key_generation():
    """Test that ACE key generation works with the correct field names."""
    
    # Mock ACE data that matches the real structure
    test_ace = {
        "trustee": {
            "name": "manderson",
            "domain": "SHAREGUARD", 
            "sid": "S-1-5-21-1923339626-2680576837-3225702567-9749",
            "full_name": "SHAREGUARD\\manderson",
            "account_type": "User",
            "is_system": False
        },
        "type": "Allow",
        "inherited": False,  # This is the correct field name
        "is_system": False,
        "permissions": {
            "Advanced": ["Read Permissions"],
            "Directory": ["List Folder", "Read Attributes", "Read Extended Attributes", "Traverse Folder"]
        }
    }
    
    # Test the change monitor service
    monitor = ChangeMonitorService()
    
    # Generate ACE key
    key = monitor._ace_key(test_ace)
    
    expected_key = "S-1-5-21-1923339626-2680576837-3225702567-9749_Allow_False"
    
    print(f"🔍 Testing ACE Key Generation")
    print(f"Expected key: {expected_key}")
    print(f"Generated key: {key}")
    print(f"Match: {key == expected_key}")
    
    if key == expected_key:
        print(f"✅ ACE key generation is working correctly!")
        return True
    else:
        print(f"❌ ACE key generation is not working correctly!")
        return False

def test_change_analysis():
    """Test the change analysis function."""
    
    # Create test permission data
    old_perms = {
        "owner": {"full_name": "SHAREGUARD\\Administrator"},
        "inheritance_enabled": True,
        "aces": [
            {
                "trustee": {"sid": "S-1-5-21-1923339626-2680576837-3225702567-1001", "full_name": "SHAREGUARD\\john.doe"},
                "type": "Allow",
                "inherited": False,
                "permissions": {"Directory": ["List Folder", "Read Attributes"]}
            }
        ]
    }
    
    new_perms = {
        "owner": {"full_name": "SHAREGUARD\\Administrator"},
        "inheritance_enabled": True,
        "aces": [
            {
                "trustee": {"sid": "S-1-5-21-1923339626-2680576837-3225702567-1001", "full_name": "SHAREGUARD\\john.doe"},
                "type": "Allow",
                "inherited": False,
                "permissions": {"Directory": ["List Folder", "Read Attributes"]}
            },
            {
                "trustee": {"sid": "S-1-5-21-1923339626-2680576837-3225702567-9749", "full_name": "SHAREGUARD\\manderson"},
                "type": "Allow", 
                "inherited": False,
                "permissions": {"Directory": ["List Folder", "Read Attributes", "Traverse Folder"]}
            }
        ]
    }
    
    monitor = ChangeMonitorService()
    changes = monitor._analyze_permission_changes(old_perms, new_perms)
    
    print(f"\\n🔍 Testing Change Analysis")
    print(f"Permissions added: {len(changes['permissions_added'])}")
    print(f"Permissions removed: {len(changes['permissions_removed'])}")
    print(f"Permissions modified: {len(changes['permissions_modified'])}")
    
    if changes['permissions_added']:
        print(f"✅ Change analysis detected permission addition:")
        for perm in changes['permissions_added']:
            print(f"  - {perm['trustee']}: {perm['permissions']}")
        return True
    else:
        print(f"❌ Change analysis failed to detect permission addition!")
        return False

if __name__ == "__main__":
    print("🚀 Testing ACE Key Fix\\n")
    
    key_test_passed = test_ace_key_generation()
    analysis_test_passed = test_change_analysis()
    
    print(f"\\n📊 Test Results:")
    print(f"ACE Key Generation: {'✅ PASS' if key_test_passed else '❌ FAIL'}")
    print(f"Change Analysis: {'✅ PASS' if analysis_test_passed else '❌ FAIL'}")
    
    if key_test_passed and analysis_test_passed:
        print(f"\\n🎉 All tests passed! The ACE key fix is working correctly.")
        sys.exit(0)
    else:
        print(f"\\n❌ Some tests failed. The fix needs more work.")
        sys.exit(1)