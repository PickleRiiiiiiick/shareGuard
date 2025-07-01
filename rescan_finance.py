import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scanner.file_scanner import FileScanner
from src.db.session import SessionLocal
from src.db.models import ScanResult
import json
from datetime import datetime

def rescan_finance():
    """Rescan the Finance folder to pick up the new inheritance detection."""
    db = SessionLocal()
    try:
        path = "C:\\ShareGuardTest\\Finance"
        print(f"Rescanning {path}...")
        
        # Initialize scanner
        scanner = FileScanner()
        
        # Perform scan
        result = scanner.scan_path(path, max_depth=5)
        
        if result['success']:
            print("Scan successful!")
            
            # Check if inheritance_enabled is in the result
            permissions = result.get('permissions', {})
            if 'inheritance_enabled' in permissions:
                print(f"Inheritance enabled: {permissions['inheritance_enabled']}")
            else:
                print("WARNING: inheritance_enabled field not found in permissions!")
                
            # Store in database
            existing = db.query(ScanResult).filter_by(path=path).first()
            if existing:
                existing.scan_time = datetime.utcnow()
                existing.data = result
                existing.success = True
                existing.error_message = None
                print("Updated existing scan result in database")
            else:
                scan_result = ScanResult(
                    path=path,
                    scan_time=datetime.utcnow(),
                    data=result,
                    success=True
                )
                db.add(scan_result)
                print("Added new scan result to database")
                
            db.commit()
            
            # Pretty print the result structure
            print("\nScan result structure:")
            print(f"- success: {result.get('success')}")
            print(f"- scan_time: {result.get('scan_time')}")
            print(f"- folder_info: {result.get('folder_info', {}).get('name')}")
            print(f"- permissions keys: {list(result.get('permissions', {}).keys())}")
            
            # Check permissions structure
            perms = result.get('permissions', {})
            print(f"\nPermissions structure:")
            print(f"- owner: {perms.get('owner', {}).get('full_name')}")
            print(f"- inheritance_enabled: {perms.get('inheritance_enabled', 'NOT FOUND')}")
            print(f"- aces count: {len(perms.get('aces', []))}")
            
        else:
            print(f"Scan failed: {result.get('error')}")
            
    except Exception as e:
        print(f"Error during rescan: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    rescan_finance()