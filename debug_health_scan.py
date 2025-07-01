#!/usr/bin/env python3
"""
Debug script to check health scan data availability
"""

import sys
sys.path.insert(0, 'src')

from db.database import SessionLocal
from db.models import ScanTarget, ScanResult
from db.models.health import HealthScan, Issue, HealthScoreHistory
from datetime import datetime

def check_data():
    db = SessionLocal()
    try:
        print("ShareGuard Health Scan Debug")
        print("=" * 50)
        
        # Check scan targets
        targets = db.query(ScanTarget).all()
        print(f"\nTotal Scan Targets: {len(targets)}")
        for target in targets:
            print(f"  - {target.path} (ID: {target.id})")
        
        # Check scan results
        results = db.query(ScanResult).all()
        print(f"\nTotal Scan Results: {len(results)}")
        
        # Group by path
        path_results = {}
        for result in results:
            if result.path not in path_results:
                path_results[result.path] = []
            path_results[result.path].append(result)
        
        print(f"Unique paths with scan results: {len(path_results)}")
        for path, scans in path_results.items():
            successful = sum(1 for s in scans if s.success)
            print(f"  - {path}: {len(scans)} scans ({successful} successful)")
            latest = max(scans, key=lambda s: s.scan_time)
            print(f"    Latest scan: {latest.scan_time} - {'Success' if latest.success else 'Failed'}")
        
        # Check health scans
        health_scans = db.query(HealthScan).order_by(HealthScan.start_time.desc()).limit(5).all()
        print(f"\nRecent Health Scans: {len(health_scans)}")
        for scan in health_scans:
            print(f"  - ID: {scan.id}, Status: {scan.status}, Score: {scan.overall_score}, Issues: {scan.issues_found}")
            if scan.scan_parameters:
                params = scan.scan_parameters
                if 'target_paths' in params:
                    print(f"    Target paths: {len(params['target_paths'])}")
        
        # Check issues
        issues = db.query(Issue).limit(10).all()
        print(f"\nTotal Issues: {db.query(Issue).count()}")
        
        # Check health score history
        scores = db.query(HealthScoreHistory).order_by(HealthScoreHistory.timestamp.desc()).limit(5).all()
        print(f"\nRecent Health Scores:")
        for score in scores:
            print(f"  - {score.timestamp}: Score={score.score}, Issues={score.issue_count}")
        
        # Recommendation
        print("\n" + "=" * 50)
        if not results:
            print("ISSUE: No scan results found!")
            print("SOLUTION: You need to run a permission scan first:")
            print("  1. Go to the /targets page")
            print("  2. Click the scan button on your target")
            print("  3. Wait for the scan to complete")
            print("  4. Then run the health scan")
        elif not path_results:
            print("ISSUE: Scan results exist but no valid paths!")
        else:
            print("Data appears to be available for health analysis.")
            print("If health scan still fails, check the logs for errors.")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_data()