# src/api/routes/target_routes.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.db.models import ScanTarget, ScanJob
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path

router = APIRouter(
    prefix="/api/v1/targets",
    tags=["targets"],
    responses={404: {"description": "Not found"}}
)

class ScanTargetCreate(BaseModel):
    name: str
    path: str
    description: Optional[str] = None
    department: Optional[str] = None
    owner: Optional[str] = None
    sensitivity_level: Optional[str] = None
    scan_frequency: Optional[str] = "daily"
    metadata: Optional[Dict] = None
    is_sensitive: Optional[bool] = False
    max_depth: Optional[int] = 5
    exclude_patterns: Optional[Dict] = None

class ScanTargetUpdate(ScanTargetCreate):
    pass

class ScanTargetResponse(BaseModel):
    id: int
    name: str
    path: str
    description: Optional[str]
    department: Optional[str]
    owner: Optional[str]
    sensitivity_level: Optional[str]
    scan_frequency: str
    is_sensitive: bool
    created_at: datetime
    last_scan_time: Optional[datetime]

@router.post("/", response_model=ScanTargetResponse, status_code=201, summary="Create Scan Target")
async def create_target(
    target: ScanTargetCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new scan target with the following fields:
    - name: Friendly name for the target
    - path: Full filesystem path to scan
    - description: Optional description
    - scan_frequency: Frequency of automatic scans
    """
    try:
        # Validate path exists
        if not Path(target.path).exists():
            raise HTTPException(
                status_code=400,
                detail="Path does not exist"
            )
        
        # Check if target already exists
        existing = db.query(ScanTarget).filter(
            (ScanTarget.name == target.name) | 
            (ScanTarget.path == target.path)
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Target with this name or path already exists"
            )
        
        # Create new target
        db_target = ScanTarget(
            name=target.name,
            path=target.path,
            description=target.description,
            department=target.department,
            owner=target.owner,
            sensitivity_level=target.sensitivity_level,
            scan_frequency=target.scan_frequency,
            metadata=target.metadata,
            is_sensitive=target.is_sensitive,
            max_depth=target.max_depth,
            exclude_patterns=target.exclude_patterns,
            created_at=datetime.utcnow(),
            last_scan_time=None
        )
        
        db.add(db_target)
        db.commit()
        db.refresh(db_target)
        
        return db_target
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/", response_model=List[ScanTargetResponse], summary="List Scan Targets")
async def list_targets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all configured scan targets.
    
    - Supports pagination with skip/limit
    - Returns basic target information
    - Ordered by creation date
    """
    targets = db.query(ScanTarget).offset(skip).limit(limit).all()
    return targets

@router.get("/{target_id}", response_model=ScanTargetResponse, summary="Get Scan Target")
async def get_target(target_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific scan target.
    
    - Includes all target configuration
    - Shows last scan time
    - Includes sensitivity and metadata
    """
    target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target

@router.put("/{target_id}", response_model=ScanTargetResponse, summary="Update Scan Target")
async def update_target(
    target_id: int,
    target: ScanTargetUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing scan target's configuration.
    
    - Can update any target attributes
    - Validates path existence
    - Maintains scan history
    """
    db_target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
    if not db_target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    # Validate new path if it's being changed
    if target.path != db_target.path and not Path(target.path).exists():
        raise HTTPException(
            status_code=400,
            detail="New path does not exist"
        )
    
    # Update fields
    for key, value in target.dict(exclude_unset=True).items():
        setattr(db_target, key, value)
    
    try:
        db.commit()
        db.refresh(db_target)
        return db_target
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.delete("/{target_id}", summary="Delete Scan Target")
async def delete_target(target_id: int, db: Session = Depends(get_db)):
    """
    Delete a scan target from the system.
    
    - Removes target configuration
    - Maintains historical scan results
    - Cannot be undone
    """
    target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    try:
        db.delete(target)
        db.commit()
        return {"message": "Target deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/{target_id}/disable", summary="Disable Scan Target")
async def disable_target(target_id: int, db: Session = Depends(get_db)):
    """
    Disable a scan target temporarily.
    
    - Prevents new scans
    - Maintains configuration
    - Can be re-enabled later
    """
    target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    target.scan_frequency = "disabled"
    db.commit()
    return {"message": "Target disabled successfully"}

@router.post("/{target_id}/enable", summary="Enable Scan Target")
async def enable_target(
    target_id: int,
    scan_frequency: str = "daily",
    db: Session = Depends(get_db)
):
    """
    Re-enable a disabled scan target.
    
    - Allows new scans to be performed
    - Can set new scan frequency
    - Resets disabled status
    """
    target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    target.scan_frequency = scan_frequency
    db.commit()
    return {"message": "Target enabled successfully"}

@router.get("/{target_id}/history", summary="Get Target Scan History")
async def get_target_history(target_id: int, db: Session = Depends(get_db)):
    """
    Get scan history for a specific target.
    
    - Lists all past scans
    - Includes success/failure status
    - Shows scan timing information
    """
    target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    scan_jobs = db.query(ScanJob).filter(ScanJob.target_id == target_id).all()
    
    return {
        "target": {
            "id": target.id,
            "name": target.name,
            "path": target.path
        },
        "scan_history": [
            {
                "job_id": job.id,
                "status": job.status,
                "start_time": job.start_time,
                "end_time": job.end_time,
                "error_message": job.error_message
            }
            for job in scan_jobs
        ]
    }