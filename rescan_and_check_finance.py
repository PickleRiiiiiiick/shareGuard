#!/usr/bin/env python3
"""
Rescan Finance folder and check if broken inheritance is detected
"""

import sys
sys.path.insert(0, 'src')

from db.database import SessionLocal
from db.models import ScanResult, ScanTarget
from core.scanner import ShareGuardScanner
from core.health_analyzer import HealthAnalyzer
from datetime import datetime
import json

def rescan_and_check():
    db = SessionLocal()
    scanner = ShareGuardScanner()
    analyzer = HealthAnalyzer()
    
    try:
        finance_path = "C:\\ShareGuardTest\\Finance"
        
        print("Rescanning Finance Folder with Inheritance Detection")
        print("=" * 60)
        
        # Run the scan
        print(f"\n1. Scanning {finance_path}...")
        result = scanner.scan_path(finance_path)
        
        if result.get('success'):
            # Save to database
            scan_result = ScanResult(
                path=finance_path,
                scan_time=datetime.utcnow(),
                success=True,
                permissions=result,
                error_message=None
            )
            
            db.add(scan_result)
            db.commit()
            
            # Print scan results
            permissions = result.get('permissions', {})
            inheritance_enabled = permissions.get('inheritance_enabled', None)
            
            print(f"✓ Scan completed successfully!")
            print(f"  Inheritance Enabled: {inheritance_enabled}")
            print(f"  ACEs found: {len(permissions.get('aces', []))}")
            
            if inheritance_enabled == False:
                print("  ⚠️  INHERITANCE IS DISABLED!")
            
            # Now run health analysis on this specific path
            print(f"\n2. Running health analysis...")
            print("-" * 40)
            
            # Analyze just this path
            issues = analyzer._analyze_path_results(finance_path, result, 999)
            
            print(f"\nRaw issues found: {len(issues)}")
            for issue in issues:
                print(f"  - {issue['issue_type'].value}: {issue['title']}")
            
            # Check specifically for broken inheritance
            inheritance_issues = [i for i in issues if i['issue_type'].value == 'broken_inheritance']
            if inheritance_issues:
                print(f"\n✓ BROKEN INHERITANCE DETECTED!")
                for issue in inheritance_issues:
                    print(f"  Title: {issue['title']}")
                    print(f"  Description: {issue['description']}")
            else:
                print(f"\n✗ No broken inheritance issue detected")
                print(f"  Debug: inheritance_enabled = {inheritance_enabled}")
            
            # Now run a full health scan
            print(f"\n3. Running full health scan...")
            scan_id = analyzer.run_health_scan([finance_path])
            print(f"Health scan completed with ID: {scan_id}")
            
            # Get the health score
            health_info = analyzer.get_health_score()
            print(f"\nHealth Score: {health_info['score']}")
            print(f"Total Issues: {health_info['issues']['total']}")
            
            # Get specific issues for Finance
            issues_result = analyzer.get_issues(path_filter="Finance")
            print(f"\nIssues for Finance folder: {issues_result['total']}")
            
            for issue in issues_result['issues']:
                print(f"\n  Issue: {issue['title']}")
                print(f"  Type: {issue['type']}")
                print(f"  Severity: {issue['severity']}")
                print(f"  Description: {issue['description']}")
            
        else:
            print(f"✗ Scan failed: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    rescan_and_check()