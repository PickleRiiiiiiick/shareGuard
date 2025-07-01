#!/usr/bin/env python3
"""
Test the health analyzer directly with Finance folder data
"""

import sys
sys.path.insert(0, 'src')

from db.database import SessionLocal
from db.models import ScanResult
from core.health_analyzer import HealthAnalyzer
import json

def test_health_analyzer():
    db = SessionLocal()
    analyzer = HealthAnalyzer()
    
    try:
        print("Testing Health Analyzer on Finance Folder")
        print("=" * 60)
        
        # Get the Finance folder scan result
        finance_scan = db.query(ScanResult).filter(
            ScanResult.path == "C:\\ShareGuardTest\\Finance",
            ScanResult.success == True
        ).order_by(ScanResult.scan_time.desc()).first()
        
        if not finance_scan:
            print("No successful scan found for C:\\ShareGuardTest\\Finance")
            return
            
        permissions = finance_scan.permissions
        print(f"Scan data from: {finance_scan.scan_time}")
        print(f"ACEs found: {len(permissions.get('aces', []))}")
        
        # Test the analyzer methods directly
        print("\n" + "-" * 40)
        print("Testing _check_direct_user_aces:")
        print("-" * 40)
        
        aces = permissions.get('aces', [])
        direct_user_issues = analyzer._check_direct_user_aces("C:\\ShareGuardTest\\Finance", aces)
        
        if direct_user_issues:
            print(f"Found {len(direct_user_issues)} direct user ACE issues:")
            for issue in direct_user_issues:
                print(f"\n  Issue Type: {issue['issue_type']}")
                print(f"  Severity: {issue['severity']}")
                print(f"  Title: {issue['title']}")
                print(f"  Description: {issue['description']}")
                print(f"  Affected Users: {', '.join(issue.get('affected_principals', []))}")
        else:
            print("No direct user ACE issues detected")
            
            # Let's debug why
            print("\nDEBUG: Analyzing ACEs...")
            user_count = 0
            for i, ace in enumerate(aces):
                trustee = ace.get('trustee', {})
                if trustee.get('type') == 'user':
                    user_count += 1
                    print(f"  ACE {i}: User={trustee.get('name')}, System={trustee.get('is_system', False)}")
            
            print(f"\nTotal user ACEs: {user_count}")
            print(f"Threshold for issue: {analyzer.config.max_direct_user_aces}")
        
        # Test other checks
        print("\n" + "-" * 40)
        print("Testing _check_broken_inheritance:")
        print("-" * 40)
        
        inheritance_issue = analyzer._check_broken_inheritance("C:\\ShareGuardTest\\Finance", permissions)
        if inheritance_issue:
            print("Found inheritance issue:")
            print(f"  Title: {inheritance_issue['title']}")
        else:
            print(f"No inheritance issue (inheritance_enabled = {permissions.get('inheritance_enabled', 'Unknown')})")
        
        # Run full path analysis
        print("\n" + "-" * 40)
        print("Running full path analysis:")
        print("-" * 40)
        
        all_issues = analyzer._analyze_path_results("C:\\ShareGuardTest\\Finance", permissions, 999)
        print(f"\nTotal issues found: {len(all_issues)}")
        
        for i, issue in enumerate(all_issues):
            print(f"\nIssue {i+1}:")
            print(f"  Type: {issue['issue_type']}")
            print(f"  Severity: {issue['severity']}")
            print(f"  Title: {issue['title']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_health_analyzer()