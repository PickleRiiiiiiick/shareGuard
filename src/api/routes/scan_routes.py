# src/api/routes/scan_routes.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime
from src.core.scanner import ShareGuardScanner
from src.db.database import get_db, SessionLocal
from src.db.models import ScanTarget, ScanJob, ScanResult, AccessEntry
from src.api.schemas import ScanRequest
from pathlib import Path
from config.settings import SCANNER_CONFIG

router = APIRouter(
    prefix="/api/v1/scan",
    tags=["scanning"],
    responses={404: {"description": "Not found"}}
)

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

async def run_scan_job(
    job_id: int, 
    path: str, 
    include_subfolders: bool, 
    max_depth: Optional[int],
    simplified_system: bool = True,
    include_inherited: bool = True
):
    """Background task to run the scan job."""
    db = SessionLocal()
    try:
        # Get the job
        job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
        if not job:
            return
        
        # Run the scan with new parameters
        scan_results = scanner.scan_path(
            path=path, 
            include_subfolders=include_subfolders, 
            max_depth=max_depth,
            simplified_system=simplified_system,
            include_inherited=include_inherited
        )
        
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
        
        # Store individual access entries
        if scan_results.get('success', True):
            for ace in scan_results.get('permissions', {}).get('aces', []):
                entry = AccessEntry(
                    scan_result_id=result.id,
                    trustee_name=ace['trustee']['name'],
                    trustee_domain=ace['trustee']['domain'],
                    trustee_sid=ace['trustee']['sid'],
                    access_type=ace['type'],
                    inherited=ace['inherited'],
                    permissions=ace['permissions']
                )
                db.add(entry)
        
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

@router.post("/path", summary="Start Path Scan")
async def scan_path(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start a new path scan job.
    
    - Scans the specified path for permissions
    - Can include subfolders recursively
    - Configurable scan depth
    - Options for system account handling and inherited permissions
    - Returns job ID for tracking
    """
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
                'max_depth': request.max_depth,
                'simplified_system': request.simplified_system,
                'include_inherited': request.include_inherited
            },
            db=db
        )

        # Start background scan with all parameters
        background_tasks.add_task(
            run_scan_job,
            job.id,
            str(path),
            request.include_subfolders,
            request.max_depth,
            request.simplified_system,
            request.include_inherited
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

@router.get("/jobs/{job_id}", summary="Get Scan Job Status")
async def get_scan_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get the status and results of a specific scan job.
    
    - Returns job details
    - Includes scan results if completed
    - Shows error information if failed
    - Includes detailed access entries
    """
    job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found")
        
    results = db.query(ScanResult).filter(ScanResult.job_id == job_id).all()
    
    # Get access entries for each result
    detailed_results = []
    for result in results:
        access_entries = db.query(AccessEntry).filter(
            AccessEntry.scan_result_id == result.id
        ).all()
        
        detailed_results.append({
            "id": result.id,
            "path": result.path,
            "scan_time": result.scan_time,
            "success": result.success,
            "error_message": result.error_message,
            "permissions": result.permissions,
            "access_entries": [
                {
                    "trustee_name": entry.trustee_name,
                    "trustee_domain": entry.trustee_domain,
                    "trustee_sid": entry.trustee_sid,
                    "access_type": entry.access_type,
                    "inherited": entry.inherited,
                    "permissions": entry.permissions
                }
                for entry in access_entries
            ]
        })
    
    return {
        "job": {
            "id": job.id,
            "status": job.status,
            "start_time": job.start_time,
            "end_time": job.end_time,
            "error_message": job.error_message,
            "parameters": job.parameters
        },
        "results": detailed_results
    }

@router.post("/clear-cache", summary="Clear Scanner Cache")
async def clear_scanner_cache():
    """
    Clear the scanner's group resolver cache.
    
    - Resets all cached group memberships
    - Forces fresh data collection on next scan
    - Useful after group membership changes
    """
    scanner.group_resolver.clear_cache()
    return {"message": "Scanner cache cleared successfully"}

@router.get("/stats", summary="Get Scanner Statistics")
async def get_scanner_stats(db: Session = Depends(get_db)):
    """
    Get scanner statistics and cache information.
    
    - Total jobs run
    - Success/failure rates
    - Cache statistics
    - Recent scan information
    """
    total_jobs = db.query(ScanJob).count()
    successful_jobs = db.query(ScanJob).filter(ScanJob.status == 'completed').count()
    failed_jobs = db.query(ScanJob).filter(ScanJob.status == 'failed').count()
    
    cache = scanner.group_resolver._cache
    
    recent_scans = (
        db.query(ScanJob)
        .order_by(ScanJob.start_time.desc())
        .limit(5)
        .all()
    )
    
    return {
        "jobs": {
            "total": total_jobs,
            "successful": successful_jobs,
            "failed": failed_jobs,
            "success_rate": (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0
        },
        "cache": {
            "groups_cached": len(cache.get('groups', {})),
            "users_cached": len(cache.get('users', {})),
            "paths_cached": len(cache.get('paths', {})),
            "memberships_cached": len(cache.get('memberships', {})),
            "group_members_cached": len(cache.get('group_members', {})),
        },
        "recent_scans": [
            {
                "id": job.id,
                "path": job.parameters.get('path'),
                "status": job.status,
                "start_time": job.start_time,
                "duration": (job.end_time - job.start_time).total_seconds() if job.end_time else None
            }
            for job in recent_scans
        ]
    }