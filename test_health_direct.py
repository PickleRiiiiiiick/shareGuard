#!/usr/bin/env python3
"""
Direct test of health analyzer to see the actual error
"""
import sys
import os

# Add src to path to match how the backend runs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set environment variables like the backend
os.environ['USE_SQLITE'] = 'true'
os.environ['SQLITE_PATH'] = 'shareguard.db'

try:
    print("Testing direct health analyzer import...")
    from core.health_analyzer import HealthAnalyzer
    print("SUCCESS: HealthAnalyzer imported successfully")
    
    print("Testing HealthAnalyzer instantiation...")
    analyzer = HealthAnalyzer()
    print("SUCCESS: HealthAnalyzer instantiated successfully")
    
    print("Testing run_health_scan method with empty path list...")
    # This should reproduce the exact error from the API endpoint
    try:
        result = analyzer.run_health_scan([])
        print(f"SUCCESS: Health scan completed: {result}")
    except Exception as e:
        print(f"ERROR: Health scan failed: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"ERROR: Import/setup failed: {e}")
    import traceback
    traceback.print_exc()