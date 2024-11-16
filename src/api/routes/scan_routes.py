# src/api/routes/scan_routes.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime
from src.core.scanner import ShareGuardScanner
from src.db.database import get_db, SessionLocal  # Add SessionLocal import
from src.db.models import ScanTarget, ScanJob, ScanResult, AccessEntry
from src.api.schemas import ScanRequest
from pathlib import Path
from config.settings import SCANNER_CONFIG

router = APIRouter(prefix="/api/v1/scan", tags=["scan"])
scanner = ShareGuardScanner()

def get_scan_target(path: str, db: Session) -> Optional[ScanTarget]:
    """Get existing scan target by path."""
    return db.query(ScanTarget).filter(ScanTarget.path == path).first()

def create_scan_job(path: str, parameters: Dict, db: Session) -> ScanJob:
    """Create a new scan job."""
    # Check if we require pre-approved targets
    require_approved_targets = SCANNER_CONFIG.get('require_approved_targets', True)
    
    # Try to find existing target
    target = get_scan_target(path, db)
    
    if not target and require_approved_targets:
        raise HTTPException(
            status_code=404,
            detail="Path is not in the list of approved scan targets. Please contact your administrator."
        )
    elif not target and not require_approved_targets:
        # Create temporary target for ad-hoc scan
        target = ScanTarget(
            name=f"Temporary-{Path(path).name}",
            path=path,
            scan_frequency="once",
            max_depth=parameters.get('max_depth'),
            last_scan_time=datetime.utcnow(),
            is_sensitive=False,  # Default for ad-hoc scans
            exclude_patterns=None  # No exclusions for ad-hoc scans
        )
        db.add(target)
        db.commit()
        db.refresh(target)

    # Validate target status if it exists
    if target.scan_frequency == "disabled":
        raise HTTPException(
            status_code=403,
            detail="This scan target has been disabled. Please contact your administrator."
        )

    # Create the scan job
    job = ScanJob(
        target_id=target.id,
        scan_type='path',
        parameters=parameters,
        status='running',
        start_time=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

async def run_scan_job(job_id: int, path: str, include_subfolders: bool, max_depth: Optional[int]):
    """Background task to run the scan job."""
    db = SessionLocal()  # Create a new session for the background task
    try:
        # Get the job
        job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if not job:
            return
        
        # Run the scan
        scan_results = scanner.scan_path(path, include_subfolders, max_depth)
        
        # Store results
        result = ScanResult(
            job_id=job_id,
            path=path,
            scan_time=datetime.utcnow(),
            owner=scan_results.get('owner'),
            permissions=scan_results,
            success=scan_results.get('success', True),
            error_message=scan_results.get('error')
        )
        db.add(result)
        
        # Update job status
        job.status = 'completed' if scan_results.get('success', True) else 'failed'
        job.end_time = datetime.utcnow()
        job.error_message = scan_results.get('error')
        
        db.commit()
    except Exception as e:
        # Update job status on error
        if job:
            job.status = 'failed'
            job.end_time = datetime.utcnow()
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()

@router.post("/path")
async def scan_path(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)  # Use Depends for proper dependency injection
):
    """Start a new path scan job."""
    try:
        # Validate path exists
        path = Path(request.path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Path does not exist")
        
        # Create job with target
        job = create_scan_job(
            path=str(path),
            parameters={
                'include_subfolders': request.include_subfolders,
                'max_depth': request.max_depth
            },
            db=db
        )

        # Start background scan
        background_tasks.add_task(
            run_scan_job,
            job.id,
            str(path),
            request.include_subfolders,
            request.max_depth
        )

        return {
            "message": "Scan job started",
            "job_id": job.id,
            "status": "running",
            "target": {
                "id": job.target.id,
                "name": job.target.name,
                "path": job.target.path,
                "is_temporary": job.target.scan_frequency == "once"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))