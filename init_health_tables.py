#!/usr/bin/env python3
"""
Initialize health tables in the ShareGuard database.
This script creates the necessary tables for the health monitoring feature.
"""

import sys
import os
import logging
from datetime import datetime, timezone

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from db.database import engine, SessionLocal
    from db.models.health import Issue, HealthScan, HealthMetrics, HealthScoreHistory
    from db.models.base import Base
    
    def init_health_tables():
        """Initialize health-related database tables."""
        logger.info("Starting health tables initialization...")
        
        try:
            # Create all tables
            Base.metadata.create_all(bind=engine, checkfirst=True)
            logger.info("Health tables created successfully")
            
            # Test database connection and tables
            db = SessionLocal()
            try:
                # Test each table
                tables_to_test = [
                    (HealthScan, "health_scans"),
                    (Issue, "issues"), 
                    (HealthMetrics, "health_metrics"),
                    (HealthScoreHistory, "health_score_history")
                ]
                
                for model, table_name in tables_to_test:
                    count = db.query(model).count()
                    logger.info(f"Table {table_name}: {count} records")
                
                # Create a sample health score history entry if none exists
                if db.query(HealthScoreHistory).count() == 0:
                    sample_score = HealthScoreHistory(
                        timestamp=datetime.now(timezone.utc),
                        score=0.0,
                        issue_count=0,
                        critical_count=0,
                        high_count=0,
                        medium_count=0,
                        low_count=0
                    )
                    db.add(sample_score)
                    db.commit()
                    logger.info("Created initial health score record")
                
                logger.info("Health tables initialization completed successfully")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error initializing health tables: {str(e)}")
            return False
    
    if __name__ == "__main__":
        success = init_health_tables()
        if success:
            print("✅ Health tables initialized successfully")
            sys.exit(0)
        else:
            print("❌ Failed to initialize health tables")
            sys.exit(1)

except ImportError as e:
    logger.error(f"Import error: {str(e)}")
    print("❌ Failed to import required modules. Make sure you're in the correct directory.")
    print("   Run this script from the ShareGuard root directory.")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    print(f"❌ Unexpected error: {str(e)}")
    sys.exit(1)