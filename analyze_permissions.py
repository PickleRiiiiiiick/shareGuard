#!/usr/bin/env python3
"""
Analyze permission data to see why health issues aren't being detected
"""

import sys
sys.path.insert(0, 'src')

from db.database import SessionLocal
from db.models import ScanResult
import json
from datetime import datetime

def analyze_permissions():
    db = SessionLocal()
    try:
        print("ShareGuard Permission Analysis")
        print("=" * 60)
        
        # Get the Finance folder scan result
        finance_scan = db.query(ScanResult).filter(
            ScanResult.path == "C:\\ShareGuardTest\\Finance",
            ScanResult.success == True
        ).order_by(ScanResult.scan_time.desc()).first()
        
        if not finance_scan:
            print("No successful scan found for C:\\ShareGuardTest\\Finance")
            return
            
        print(f"Analyzing scan from: {finance_scan.scan_time}")
        print(f"Success: {finance_scan.success}")
        
        permissions = finance_scan.permissions
        if not permissions:
            print("No permission data found!")
            return
            
        print(f"\nInheritance Enabled: {permissions.get('inheritance_enabled', 'Unknown')}")
        print(f"Owner: {permissions.get('owner', 'Unknown')}")
        
        aces = permissions.get('aces', [])
        print(f"\nTotal ACEs: {len(aces)}")
        
        # Analyze each ACE
        user_aces = []
        group_aces = []
        system_aces = []
        
        for i, ace in enumerate(aces):
            trustee = ace.get('trustee', {})
            trustee_type = trustee.get('type', 'unknown')
            trustee_name = trustee.get('name', 'Unknown')
            is_system = trustee.get('is_system', False)
            
            print(f"\nACE #{i+1}:")
            print(f"  Trustee: {trustee_name}")
            print(f"  Type: {trustee_type}")
            print(f"  System: {is_system}")
            print(f"  Access Type: {ace.get('access_type', 'Unknown')}")
            print(f"  Permissions: {', '.join(ace.get('permissions', []))[:80]}...")
            
            if trustee_type == 'user' and not is_system:
                user_aces.append(ace)
            elif trustee_type == 'group':
                group_aces.append(ace)
            elif is_system:
                system_aces.append(ace)
        
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY:")
        print(f"- Direct User ACEs (non-system): {len(user_aces)}")
        for ace in user_aces:
            print(f"  • {ace['trustee']['name']}")
            
        print(f"\n- Group ACEs: {len(group_aces)}")
        for ace in group_aces:
            print(f"  • {ace['trustee']['name']}")
            
        print(f"\n- System ACEs: {len(system_aces)}")
        
        print("\n" + "=" * 60)
        print("EXPECTED ISSUES:")
        if len(user_aces) > 0:
            print(f"✗ Direct User ACEs: {len(user_aces)} users have direct permissions")
            print("  This should trigger a 'direct_user_ace' issue in health scan")
        
        if not permissions.get('inheritance_enabled', True):
            print("✗ Inheritance Disabled")
            print("  This should trigger a 'broken_inheritance' issue")
            
        # Save the raw data for inspection
        with open('finance_permissions.json', 'w') as f:
            json.dump(permissions, f, indent=2)
        print("\nRaw permission data saved to: finance_permissions.json")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    analyze_permissions()