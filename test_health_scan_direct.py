#!/usr/bin/env python3
"""
Test health scan functionality directly without API
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db.database import SessionLocal
from core.health_analyzer import HealthAnalyzer
from db.models import ScanResult
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_health_scan():
    """Test health scan with existing data"""
    db = SessionLocal()
    try:
        # Check for existing scan results
        existing_paths = db.query(ScanResult.path).distinct().limit(10).all()
        print(f"Found {len(existing_paths)} existing scan results")
        
        if existing_paths:
            print("Sample paths:")
            for path in existing_paths[:5]:
                print(f"  - {path[0]}")
        
        # Initialize health analyzer
        analyzer = HealthAnalyzer()
        
        # Get current health score
        print("\nGetting current health score...")
        score_data = analyzer.get_health_score()
        print(f"Health Score: {score_data}")
        
        if existing_paths:
            print("\nRunning health scan on first 3 paths...")
            target_paths = [path[0] for path in existing_paths[:3]]
            scan_id = analyzer.run_health_scan(target_paths)
            print(f"Scan completed with ID: {scan_id}")
            
            # Get updated score
            print("\nUpdated health score:")
            new_score = analyzer.get_health_score()
            print(f"Health Score: {new_score}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_health_scan()