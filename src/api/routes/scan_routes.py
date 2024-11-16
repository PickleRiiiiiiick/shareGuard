# src/api/routes/scan_routes.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime
from src.core.scanner import ShareGuardScanner
from src.db.database import get_db
from src.db.models import ScanJob, ScanResult, AccessEntry, ScanTarget
from src.api.schemas import ScanRequest

router = APIRouter(prefix="/api/v1/scan", tags=["scan"])
scanner = ShareGuardScanner()

def create_scan_job(db: Session, scan_type: str, target_name: str, parameters: Dict) -> ScanJob:
    """Create a new scan job in the database."""
    target = db.query(ScanTarget).filter(ScanTarget.name == target_name).first()
    if not target:
        raise HTTPException(status_code=404, detail="Scan target not found")

    job = ScanJob(
        scan_type=scan_type,
        target_id=target.id,  # Referencing the target_id foreign key to ScanTarget
        parameters=parameters,
        status='running',
        start_time=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

async def run_scan_job(job_id: int, path: str, include_subfolders: bool, max_depth: Optional[int], db: Session):
    """Background task to run scan job."""
    try:
        results = scanner.scan_path(path, include_subfolders, max_depth)
        
        # Get job from database
        job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if not job:
            return
        
        # Create scan result
        result = ScanResult(
            job_id=job.id,
            path=path,
            owner=results.get('owner'),
            permissions=results.get('permissions', {}),  # Assuming permissions are structured correctly
            success=results.get('success', True),
            error_message=results.get('error'),
            scan_time=datetime.utcnow()
        )
        db.add(result)
        
        # Update job status
        job.status = 'completed'
        job.end_time = datetime.utcnow()
        
        db.commit()
    except Exception as e:
        job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if job:
            job.status = 'failed'
            job.error_message = str(e)
            job.end_time = datetime.utcnow()
            db.commit()

@router.post("/path")
async def scan_path(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a new path scan job."""
    try:
        # Create scan job using the helper function
        job = create_scan_job(
            db=db,
            scan_type='path',
            target_name=request.path,  # Adjusted to use path as target_name
            parameters={
                'include_subfolders': request.include_subfolders,
                'max_depth': request.max_depth
            }
        )

        # Start background scan
        background_tasks.add_task(
            run_scan_job,
            job.id,
            request.path,
            request.include_subfolders,
            request.max_depth,
            db
        )

        return {
            "message": "Scan job started",
            "job_id": job.id,
            "status": "running"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{job_id}")
async def get_scan_results(job_id: int, db: Session = Depends(get_db)):
    """Get results of a scan job."""
    try:
        job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Scan job not found")
        
        results = db.query(ScanResult).filter(ScanResult.job_id == job_id).all()
        
        return {
            "job_info": {
                "id": job.id,
                "status": job.status,
                "start_time": job.start_time,
                "end_time": job.end_time,
                "target": job.target.name,  # Show the target name
                "parameters": job.parameters
            },
            "results": [
                {
                    "path": result.path,
                    "scan_time": result.scan_time,
                    "success": result.success,
                    "permissions": result.permissions
                }
                for result in results
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
