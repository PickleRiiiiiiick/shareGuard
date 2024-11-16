# src/api/routes/target_routes.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.db.models import ScanTarget
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
from pathlib import Path

router = APIRouter(prefix="/api/v1/targets", tags=["targets"])

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

@router.post("/", status_code=201)
def create_target(
    target: ScanTargetCreate,
    db: Session = Depends(get_db)
):
    """Create a new scan target."""
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
        
        return {
            "message": "Scan target created successfully",
            "target": {
                "id": db_target.id,
                "name": db_target.name,
                "path": db_target.path,
                "scan_frequency": db_target.scan_frequency,
                "created_at": db_target.created_at
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/")
def list_targets(db: Session = Depends(get_db)):
    """List all scan targets."""
    return db.query(ScanTarget).all()

@router.get("/{target_id}")
def get_target(target_id: int, db: Session = Depends(get_db)):
    """Get a specific scan target."""
    target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target

@router.delete("/{target_id}")
def delete_target(target_id: int, db: Session = Depends(get_db)):
    """Delete a scan target."""
    target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    db.delete(target)
    db.commit()
    return {"message": "Target deleted successfully"}