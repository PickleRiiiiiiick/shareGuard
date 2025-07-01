#!/usr/bin/env python3
"""
Diagnostic script to check what data is available for health analysis
"""

import sys
sys.path.insert(0, 'src')

from db.database import SessionLocal
from db.models import ScanTarget, ScanResult
from db.models.health import HealthScan, Issue, HealthScoreHistory
from datetime import datetime
import json

def diagnose_data():
    db = SessionLocal()
    try:
        print("ShareGuard Health Data Diagnosis")
        print("=" * 60)
        
        # Check scan targets
        targets = db.query(ScanTarget).all()
        print(f"\n1. SCAN TARGETS: {len(targets)} total")
        for target in targets:
            print(f"   - ID {target.id}: {target.path} (Active: {target.is_active})")
        
        # Check ALL scan results 
        all_results = db.query(ScanResult).all()
        print(f"\n2. SCAN RESULTS: {len(all_results)} total")
        
        if not all_results:
            print("   ❌ NO SCAN RESULTS FOUND!")
            print("   SOLUTION: You need to run a permission scan first:")
            print("   1. Go to /targets page")
            print("   2. Click 'Scan' button on a target")
            print("   3. Wait for scan to complete")
            print("   4. Then run health scan")
            return
        
        # Check successful vs failed results
        successful_results = [r for r in all_results if r.success]
        failed_results = [r for r in all_results if not r.success]
        
        print(f"   - Successful: {len(successful_results)}")
        print(f"   - Failed: {len(failed_results)}")
        
        if not successful_results:
            print("   ❌ NO SUCCESSFUL SCAN RESULTS!")
            print("   PROBLEM: All scans failed. Check scan logs for errors.")
            for result in failed_results[:3]:  # Show first 3 failed results
                print(f"      Failed scan: {result.path} - {result.error_message}")
            return
        
        # Check permissions data structure
        print(f"\n3. PERMISSIONS DATA CHECK:")
        for i, result in enumerate(successful_results[:3]):  # Check first 3 successful results
            print(f"   Result {i+1}: {result.path}")
            print(f"   - Success: {result.success}")
            print(f"   - Has permissions: {result.permissions is not None}")
            
            if result.permissions:
                if isinstance(result.permissions, dict):
                    print(f"   - Permissions type: dict")
                    print(f"   - Keys: {list(result.permissions.keys())}")
                    
                    # Check for ACE data
                    if 'aces' in result.permissions:
                        ace_count = len(result.permissions['aces'])
                        print(f"   - ACEs found: {ace_count}")
                    elif 'permissions' in result.permissions and 'aces' in result.permissions['permissions']:
                        ace_count = len(result.permissions['permissions']['aces'])
                        print(f"   - ACEs found (nested): {ace_count}")
                    else:
                        print(f"   - ❌ No ACEs found in permissions data")
                        print(f"   - Sample data: {str(result.permissions)[:200]}...")
                else:
                    print(f"   - ❌ Permissions type: {type(result.permissions)} (should be dict)")
            else:
                print(f"   - ❌ No permissions data")
        
        # Check health scans
        health_scans = db.query(HealthScan).all()
        print(f"\n4. HEALTH SCANS: {len(health_scans)} total")
        for scan in health_scans[-3:]:  # Show last 3 scans
            print(f"   - ID {scan.id}: {scan.status}, Score: {scan.overall_score}, Issues: {scan.issues_found}")
            if scan.scan_parameters and 'target_paths' in scan.scan_parameters:
                print(f"     Paths: {len(scan.scan_parameters['target_paths'])}")
        
        # Check issues
        issues = db.query(Issue).all()
        print(f"\n5. HEALTH ISSUES: {len(issues)} total")
        
        # Check health score history
        scores = db.query(HealthScoreHistory).all()
        print(f"\n6. HEALTH SCORE HISTORY: {len(scores)} total")
        
        # Final recommendation
        print("\n" + "=" * 60)
        if successful_results and any(r.permissions for r in successful_results):
            print("✅ DATA LOOKS GOOD: You have successful scan results with permissions data")
            print("🔍 DEBUG: Check the backend logs when running health scan for specific errors")
            print("📝 Look for lines containing 'health_analyzer' or 'Health scan'")
        else:
            print("❌ DATA ISSUES FOUND: See problems above")
            
    except Exception as e:
        print(f"Error during diagnosis: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    diagnose_data()