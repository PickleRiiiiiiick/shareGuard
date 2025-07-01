#!/usr/bin/env python3
"""
Run a permission scan on a specific target
"""

import sys
sys.path.insert(0, 'src')

from db.database import SessionLocal
from db.models import ScanTarget, ScanResult
from core.scanner import ShareGuardScanner
from datetime import datetime
import json

def run_scan(target_path=None):
    db = SessionLocal()
    scanner = ShareGuardScanner()
    
    try:
        # If no path provided, use the first target
        if not target_path:
            target = db.query(ScanTarget).order_by(ScanTarget.created_at.desc()).first()
            if not target:
                print("No scan targets found!")
                print("Please add a target on the /targets page first.")
                return
            target_path = target.path
            print(f"Using most recent target: {target.name}")
        
        print(f"Running permission scan on: {target_path}")
        print("-" * 50)
        
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
            
            # Check permissions structure
            permissions = result.get('permissions', {})
            
            # Get owner info
            owner_info = permissions.get('owner', {})
            owner_name = owner_info.get('name', 'Unknown') if isinstance(owner_info, dict) else 'Unknown'
            
            # Get inheritance status
            inheritance_enabled = permissions.get('inheritance_enabled', None)
            inheritance_status = 'Enabled' if inheritance_enabled else 'Disabled' if inheritance_enabled is False else 'Unknown'
            
            # Get ACEs
            aces = permissions.get('aces', [])
            
            print(f"  Owner: {owner_name}")
            print(f"  Inheritance: {inheritance_status}")
            print(f"  ACEs found: {len(aces)}")
            if aces:
                print(f"\n  First 3 ACEs:")
                for i, ace in enumerate(aces[:3]):
                    trustee = ace.get('trustee', {})
                    print(f"    {i+1}. {trustee.get('name', 'Unknown')} - {ace.get('access_type', 'Unknown')}")
        else:
            print(f"✗ Scan failed: {result.get('error', 'Unknown error')}")
        
        print("\nScan result saved to database.")
        print("You can now run the health scan to analyze this data.")
        
    except Exception as e:
        print(f"Error during scan: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run a permission scan')
    parser.add_argument('path', nargs='?', help='Path to scan (optional, uses first target if not provided)')
    args = parser.parse_args()
    
    run_scan(args.path)