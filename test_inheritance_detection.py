#!/usr/bin/env python3
"""
Test inheritance detection for folders
"""

import sys
sys.path.insert(0, 'src')

from scanner.file_scanner import PermissionScanner
import json

def test_inheritance_detection():
    scanner = PermissionScanner()
    
    # Test folders
    test_paths = [
        "C:\\ShareGuardTest\\Finance",  # Should have inheritance disabled
        "C:\\ShareGuardTest\\HR",        # Check this one too
        "C:\\ShareGuardTest\\IT",        # And this one
    ]
    
    print("Testing Inheritance Detection")
    print("=" * 60)
    
    for path in test_paths:
        print(f"\nScanning: {path}")
        print("-" * 40)
        
        try:
            result = scanner.get_folder_permissions(path)
            
            if result.get('success'):
                inheritance_enabled = result.get('inheritance_enabled', 'NOT_FOUND')
                print(f"  Inheritance Enabled: {inheritance_enabled}")
                print(f"  Owner: {result.get('owner', {}).get('name', 'Unknown')}")
                print(f"  Total ACEs: {len(result.get('aces', []))}")
                
                # Count inherited vs explicit ACEs
                aces = result.get('aces', [])
                inherited_count = sum(1 for ace in aces if ace.get('inherited', False))
                explicit_count = len(aces) - inherited_count
                
                print(f"  Inherited ACEs: {inherited_count}")
                print(f"  Explicit ACEs: {explicit_count}")
                
                if inheritance_enabled == False:
                    print("  ⚠️  INHERITANCE IS DISABLED (Broken Inheritance)")
                
            else:
                print(f"  Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"  Exception: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test complete!")

if __name__ == "__main__":
    test_inheritance_detection()