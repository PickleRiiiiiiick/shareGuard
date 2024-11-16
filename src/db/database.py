# src/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging
from config.settings import DB_CONFIG

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    DB_CONFIG['url'],
    poolclass=QueuePool,
    pool_size=DB_CONFIG['pool_size'],
    max_overflow=DB_CONFIG['max_overflow'],
    pool_timeout=DB_CONFIG['timeout']
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Database session context manager."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        db.close()

def init_db() -> None:
    """Initialize database tables."""
    from .models import Base
    Base.metadata.create_all(bind=engine)

def store_scan_job(scan_type: str, target: str, parameters: dict) -> int:
    """Create a new scan job record."""
    from .models import ScanJob
    
    with get_db() as db:
        job = ScanJob(
            scan_type=scan_type,
            target=target,
            parameters=parameters,
            status='running'
        )
        db.add(job)
        db.commit()
        return job.id

def store_scan_result(job_id: int, path: str, scan_data: dict) -> None:
    """Store scan results in the database."""
    from .models import ScanResult, AccessEntry
    
    with get_db() as db:
        # Create scan result
        result = ScanResult(
            job_id=job_id,
            path=path,
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

def update_scan_job_status(job_id: int, status: str, error_message: str = None) -> None:
    """Update scan job status."""
    from .models import ScanJob
    
    with get_db() as db:
        job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if job:
            job.status = status
            job.error_message = error_message
            # job.end_time = datetime.utcnow() if status in ['completed', 'failed'] else None