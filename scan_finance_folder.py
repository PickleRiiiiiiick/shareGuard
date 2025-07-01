#!/usr/bin/env python3
"""
Run a fresh permission scan on the Finance folder
"""

import sys
sys.path.insert(0, 'src')

from db.database import SessionLocal
from db.models import ScanResult
from core.scanner import ShareGuardScanner
from datetime import datetime
import json

def scan_finance():
    db = SessionLocal()
    scanner = ShareGuardScanner()
    
    try:
        target_path = "C:\\ShareGuardTest\\Finance"
        print(f"Running fresh permission scan on: {target_path}")
        print("-" * 60)
        
        # Run the scan
        result = scanner.scan_path(target_path)
        
        # Save to database
        scan_result = ScanResult(
            path=target_path,
            scan_time=datetime.utcnow(),
            success=result.get('success', False),
            permissions=result,
            error_message=result.get('error') if not result.get('success') else None
        )
        
        db.add(scan_result)
        db.commit()
        
        if result.get('success'):
            print(f"✓ Scan completed successfully!")
            
            # Check the permissions structure
            if 'permissions' in result and 'aces' in result['permissions']:
                aces = result['permissions']['aces']
            else:
                aces = result.get('aces', [])
                
            print(f"\nACEs found: {len(aces)}")
            
            # Look for user ACEs
            user_aces = []
            for ace in aces:
                trustee = ace.get('trustee', {})
                trustee_name = trustee.get('name', '')
                trustee_domain = trustee.get('domain', '')
                
                # Check if this looks like a user account
                if ('.' in trustee_name or '@' in trustee_name or 
                    (trustee_domain not in ['NT AUTHORITY', 'BUILTIN'] and 
                     not trustee_name.endswith('_Staff') and 
                     not trustee_name.endswith('_Viewers'))):
                    user_aces.append(trustee_name)
                    print(f"  • User ACE: {trustee.get('full_name', trustee_name)}")
            
            if user_aces:
                print(f"\n⚠️  Found {len(user_aces)} direct user permissions!")
                print("These should be detected as issues in the health scan.")
            else:
                print("\nNo obvious direct user permissions found.")
                print("Check if john.smith and Benjamin Anderson are in the ACE list above.")
                
            # Save detailed scan for inspection
            with open('finance_scan_latest.json', 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nDetailed scan saved to: finance_scan_latest.json")
        else:
            print(f"✗ Scan failed: {result.get('error', 'Unknown error')}")
        
        print(f"\nNow run the health scan to analyze this fresh data:")
        print("1. Go to /health page")
        print("2. Click 'Run New Scan'")
        print("3. Check if direct user ACE issues are detected")
        
    except Exception as e:
        print(f"Error during scan: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    scan_finance()