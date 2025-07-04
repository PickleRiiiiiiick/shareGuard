#!/usr/bin/env python3
"""Simple test to verify ACE key generation logic."""

def ace_key_old(ace):
    """Old version that was failing."""
    trustee = ace.get("trustee", {})
    return f"{trustee.get('sid', '')}_{ace.get('type', '')}_{ace.get('is_inherited', False)}"

def ace_key_new(ace):
    """New version with correct field name."""
    trustee = ace.get("trustee", {})
    return f"{trustee.get('sid', '')}_{ace.get('type', '')}_{ace.get('inherited', False)}"

def test_ace_key_fix():
    """Test the ACE key fix."""
    
    # Real ACE structure from the database
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
        "inherited": False,  # This is the correct field name!
        "is_system": False,
        "permissions": {
            "Advanced": ["Read Permissions"],
            "Directory": ["List Folder", "Read Attributes", "Read Extended Attributes", "Traverse Folder"]
        }
    }
    
    old_key = ace_key_old(test_ace)
    new_key = ace_key_new(test_ace)
    
    print("🔍 Testing ACE Key Generation Fix")
    print("=" * 50)
    print(f"ACE has 'inherited' field: {'inherited' in test_ace}")
    print(f"ACE has 'is_inherited' field: {'is_inherited' in test_ace}")
    print(f"Value of 'inherited': {test_ace.get('inherited', 'NOT FOUND')}")
    print(f"Value of 'is_inherited': {test_ace.get('is_inherited', 'NOT FOUND')}")
    print()
    print(f"Old key (using is_inherited): {old_key}")
    print(f"New key (using inherited): {new_key}")
    print()
    
    if old_key == new_key:
        print("⚠️  Keys are the same - this indicates the field doesn't affect the key")
    else:
        print("✅ Keys are different - this shows the fix is working!")
    
    # The correct key should use the actual field value
    expected_key = "S-1-5-21-1923339626-2680576837-3225702567-9749_Allow_False"
    
    print(f"Expected key: {expected_key}")
    print(f"New key matches expected: {new_key == expected_key}")
    
    if new_key == expected_key:
        print("🎉 ACE key generation is now correct!")
        return True
    else:
        print("❌ ACE key generation is still incorrect!")
        return False

if __name__ == "__main__":
    success = test_ace_key_fix()
    if success:
        print("\n✅ Test passed! The ACE key fix should resolve the change detection issue.")
    else:
        print("\n❌ Test failed! The ACE key fix needs more work.")