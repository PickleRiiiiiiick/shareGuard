# src/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
from datetime import datetime
import logging
from config.settings import DB_CONFIG

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    DB_CONFIG['url'],
    poolclass=QueuePool,
    pool_size=DB_CONFIG['pool_size'],
    max_overflow=DB_CONFIG['max_overflow'],
    pool_timeout=DB_CONFIG['timeout'],
    pool_recycle=DB_CONFIG['pool_recycle'],
    fast_executemany=DB_CONFIG['fast_executemany']
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Initialize database tables."""
    from .models import Base
    Base.metadata.create_all(bind=engine)

def store_scan_job(scan_type: str, target: str, parameters: dict) -> int:
    """Create a new scan job record."""
    from .models import ScanJob
    
    db = SessionLocal()
    try:
        job = ScanJob(
            scan_type=scan_type,
            target=target,
            parameters=parameters,
            status='running',
            start_time=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job.id
    except Exception as e:
        logger.error(f"Error storing scan job: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def store_scan_result(job_id: int, path: str, scan_data: dict) -> None:
    """Store scan results in the database."""
    from .models import ScanResult, AccessEntry
    
    db = SessionLocal()
    try:
        # Create scan result
        result = ScanResult(
            job_id=job_id,
            path=path,
            scan_time=datetime.utcnow(),
            owner=scan_data.get('owner'),
            permissions=scan_data,
            success=scan_data.get('success', True),
            error_message=scan_data.get('error')
        )
        db.add(result)
        db.flush()  # Get result.id

        # Store individual access entries
        for ace in scan_data.get('aces', []):
            trustee = ace['trustee']
            entry = AccessEntry(
                scan_result_id=result.id,
                trustee_name=trustee['name'],
                trustee_domain=trustee['domain'],
                trustee_sid=trustee['sid'],
                access_type=ace['type'],
                inherited=ace['inherited'],
                permissions=ace['permissions']
            )
            db.add(entry)

        db.commit()
    except Exception as e:
        logger.error(f"Error storing scan result: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def update_scan_job_status(job_id: int, status: str, error_message: str = None) -> None:
    """Update scan job status."""
    from .models import ScanJob
    
    db = SessionLocal()
    try:
        job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if job:
            job.status = status
            job.error_message = error_message
            if status in ['completed', 'failed']:
                job.end_time = datetime.utcnow()
            db.commit()
    except Exception as e:
        logger.error(f"Error updating scan job status: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def get_scan_job(job_id: int) -> dict:
    """Get scan job details."""
    from .models import ScanJob
    
    db = SessionLocal()
    try:
        job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if not job:
            return None
            
        return {
            'id': job.id,
            'scan_type': job.scan_type,
            'target': job.target,
            'status': job.status,
            'start_time': job.start_time,
            'end_time': job.end_time,
            'error_message': job.error_message,
            'parameters': job.parameters
        }
    except Exception as e:
        logger.error(f"Error retrieving scan job: {str(e)}")
        raise
    finally:
        db.close()

def get_recent_scan_results(limit: int = 10) -> list:
    """Get most recent scan results."""
    from .models import ScanResult
    
    db = SessionLocal()
    try:
        results = (db.query(ScanResult)
                  .order_by(ScanResult.scan_time.desc())
                  .limit(limit)
                  .all())
                  
        return [
            {
                'id': result.id,
                'job_id': result.job_id,
                'path': result.path,
                'scan_time': result.scan_time,
                'success': result.success,
                'error_message': result.error_message
            }
            for result in results
        ]
    except Exception as e:
        logger.error(f"Error retrieving recent scan results: {str(e)}")
        raise
    finally:
        db.close()

def cleanup_old_scan_results(days_to_keep: int = 30) -> int:
    """Remove scan results older than specified days."""
    from .models import ScanResult
    from datetime import timedelta
    
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted_count = (db.query(ScanResult)
                        .filter(ScanResult.scan_time < cutoff_date)
                        .delete())
        db.commit()
        return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up old scan results: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()