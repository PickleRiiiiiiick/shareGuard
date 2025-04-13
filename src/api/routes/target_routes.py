# src/api/routes/target_routes.py

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from src.db.database import get_db
from src.db.models import ScanTarget, ScanJob
from src.api.middleware.auth import security, require_permissions
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path
from src.utils.logger import setup_logger

logger = setup_logger('target_routes')

router = APIRouter(
    prefix="/targets",
    tags=["targets"],
    dependencies=[Depends(security)]
)


class ScanTargetCreate(BaseModel):
    name: str
    path: str
    description: Optional[str] = None
    department: Optional[str] = None
    owner: Optional[str] = None
    sensitivity_level: Optional[str] = None
    scan_frequency: Optional[str] = "daily"
    target_metadata: Optional[Dict] = None
    is_sensitive: Optional[bool] = False
    max_depth: Optional[int] = 5
    exclude_patterns: Optional[Dict] = None


class ScanTargetUpdate(ScanTargetCreate):
    pass


class ScanTargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    path: str
    description: Optional[str] = None
    department: Optional[str] = None
    owner: Optional[str] = None
    sensitivity_level: Optional[str] = None
    scan_frequency: str
    is_sensitive: bool = False
    target_metadata: Optional[Dict] = None
    created_at: datetime
    last_scan_time: Optional[datetime] = None
    created_by: Optional[str] = None


@router.post("/", response_model=ScanTargetResponse, status_code=201, summary="Create Scan Target")
@require_permissions(["targets:create"])
async def create_target(
    target: ScanTargetCreate,
    current_request: Request,
    db: Session = Depends(get_db)
):
    """Create a new scan target."""
    try:
        logger.debug(f"Attempting to create target: {target.name}")
        if not Path(target.path).exists():
            logger.error(f"Path does not exist: {target.path}")
            raise HTTPException(
                status_code=400,
                detail="Path does not exist"
            )

        existing = db.query(ScanTarget).filter(
            (ScanTarget.name == target.name) |
            (ScanTarget.path == target.path)
        ).first()

        if existing:
            logger.warning(f"Target already exists with name: {target.name} or path: {target.path}")
            raise HTTPException(
                status_code=400,
                detail="Target with this name or path already exists"
            )

        service_account = current_request.state.service_account

        db_target = ScanTarget(
            name=target.name,
            path=target.path,
            description=target.description,
            department=target.department,
            owner=target.owner,
            sensitivity_level=target.sensitivity_level,
            scan_frequency=target.scan_frequency,
            target_metadata=target.target_metadata,
            is_sensitive=target.is_sensitive,
            max_depth=target.max_depth,
            exclude_patterns=target.exclude_patterns,
            created_at=datetime.utcnow(),
            last_scan_time=None,
            created_by=service_account.username
        )

        db.add(db_target)
        db.commit()
        db.refresh(db_target)

        logger.info(f"Successfully created target: {target.name}")
        return ScanTargetResponse.model_validate(db_target)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating target")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/", response_model=List[ScanTargetResponse], summary="List Scan Targets")
@require_permissions(["targets:read"])
async def list_targets(
    current_request: Request,
    db: Session = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    sort_by: str = Query(
        default="created_at",
        description="Field to sort by",
        regex="^(id|name|created_at|last_scan_time)$"
    ),
    sort_desc: bool = Query(
        default=True,
        description="Sort in descending order"
    )
):
    """List scan targets with pagination and sorting."""
    try:
        logger.debug(f"Listing targets with params: skip={skip}, limit={limit}, sort_by={sort_by}, sort_desc={sort_desc}")

        query = db.query(ScanTarget)

        if sort_desc:
            query = query.order_by(desc(getattr(ScanTarget, sort_by)))
        else:
            query = query.order_by(getattr(ScanTarget, sort_by))

        targets = query.offset(skip).limit(limit).all()

        response_targets = []
        for target in targets:
            try:
                response_target = ScanTargetResponse.model_validate(target)
                response_targets.append(response_target)
            except Exception as e:
                logger.error(f"Error converting target {target.id}: {str(e)}")
                continue

        logger.debug(f"Retrieved {len(response_targets)} targets")
        return response_targets

    except AttributeError as e:
        logger.error(f"Invalid sort field or attribute error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort field or attribute: {str(e)}"
        )
    except Exception as e:
        logger.exception("Error retrieving targets")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving targets: {str(e)}"
        )


@router.get("/count", response_model=dict, summary="Get Total Target Count")
@require_permissions(["targets:read"])
async def get_targets_count(
    current_request: Request,
    db: Session = Depends(get_db)
):
    """Get the total number of scan targets."""
    try:
        count = db.query(ScanTarget).count()
        return {"total": count}
    except Exception as e:
        logger.exception("Error counting targets")
        raise HTTPException(
            status_code=500,
            detail=f"Error counting targets: {str(e)}"
        )


@router.get("/{target_id}", response_model=ScanTargetResponse, summary="Get Scan Target")
@require_permissions(["targets:read"])
async def get_target(
    target_id: int,
    current_request: Request,
    db: Session = Depends(get_db)
):
    """Get a specific scan target by ID."""
    try:
        logger.debug(f"Retrieving target with ID: {target_id}")
        target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
        if not target:
            logger.warning(f"Target not found with ID: {target_id}")
            raise HTTPException(status_code=404, detail="Target not found")

        return ScanTargetResponse.model_validate(target)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving target: {target_id}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.put("/{target_id}", response_model=ScanTargetResponse, summary="Update Scan Target")
@require_permissions(["targets:update"])
async def update_target(
    target_id: int,
    target: ScanTargetUpdate,
    current_request: Request,
    db: Session = Depends(get_db)
):
    """Update an existing scan target."""
    try:
        logger.debug(f"Updating target with ID: {target_id}")
        db_target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
        if not db_target:
            logger.warning(f"Target not found with ID: {target_id}")
            raise HTTPException(status_code=404, detail="Target not found")

        if target.path != db_target.path and not Path(target.path).exists():
            logger.error(f"New path does not exist: {target.path}")
            raise HTTPException(
                status_code=400,
                detail="New path does not exist"
            )

        for key, value in target.dict(exclude_unset=True).items():
            setattr(db_target, key, value)

        db.commit()
        db.refresh(db_target)
        logger.info(f"Successfully updated target: {target_id}")
        return ScanTargetResponse.model_validate(db_target)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating target: {target_id}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.delete("/{target_id}", status_code=204, summary="Delete Scan Target")
@require_permissions(["targets:delete"])
async def delete_target(
    target_id: int,
    current_request: Request,
    db: Session = Depends(get_db)
):
    """Delete a scan target."""
    try:
        logger.debug(f"Deleting target with ID: {target_id}")
        target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
        if not target:
            logger.warning(f"Target not found with ID: {target_id}")
            raise HTTPException(status_code=404, detail="Target not found")

        db.delete(target)
        db.commit()
        logger.info(f"Successfully deleted target: {target_id}")
        return None  # 204 No Content
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting target: {target_id}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/{target_id}/disable", response_model=dict, summary="Disable Scan Target")
@require_permissions(["targets:update"])
async def disable_target(
    target_id: int,
    current_request: Request,
    db: Session = Depends(get_db)
):
    """Disable scanning for a target."""
    try:
        logger.debug(f"Disabling target with ID: {target_id}")
        target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
        if not target:
            logger.warning(f"Target not found with ID: {target_id}")
            raise HTTPException(status_code=404, detail="Target not found")

        target.scan_frequency = "disabled"
        db.commit()
        logger.info(f"Successfully disabled target: {target_id}")
        return {"message": "Target disabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error disabling target: {target_id}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/{target_id}/enable", response_model=dict, summary="Enable Scan Target")
@require_permissions(["targets:update"])
async def enable_target(
    target_id: int,
    current_request: Request,
    scan_frequency: str = Query(default="daily", regex="^(hourly|daily|weekly|monthly)$"),
    db: Session = Depends(get_db)
):
    """Enable scanning for a target with specified frequency."""
    try:
        logger.debug(f"Enabling target with ID: {target_id} with frequency: {scan_frequency}")
        target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
        if not target:
            logger.warning(f"Target not found with ID: {target_id}")
            raise HTTPException(status_code=404, detail="Target not found")

        target.scan_frequency = scan_frequency
        db.commit()
        logger.info(f"Successfully enabled target: {target_id} with frequency: {scan_frequency}")
        return {"message": "Target enabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error enabling target: {target_id}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/{target_id}/history", summary="Get Target Scan History")
@require_permissions(["targets:read"])
async def get_target_history(
    target_id: int,
    current_request: Request,
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000),
    skip: int = Query(default=0, ge=0)
):
    """Get scan history for a target."""
    try:
        logger.debug(f"Retrieving history for target ID: {target_id}")
        target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
        if not target:
            logger.warning(f"Target not found with ID: {target_id}")
            raise HTTPException(status_code=404, detail="Target not found")

        scan_jobs = db.query(ScanJob)\
            .filter(ScanJob.target_id == target_id)\
            .order_by(desc(ScanJob.start_time))\
            .offset(skip)\
            .limit(limit)\
            .all()

        logger.debug(f"Retrieved {len(scan_jobs)} history records for target ID: {target_id}")
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
                    "error_message": job.error_message,
                    "created_by": job.created_by
                }
                for job in scan_jobs
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving target history: {target_id}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/{target_id}/stats", response_model=dict, summary="Get Target Statistics")
@require_permissions(["targets:read"])
async def get_target_stats(
    target_id: int,
    current_request: Request,
    db: Session = Depends(get_db)
):
    """Get statistics for a specific scan target."""
    try:
        logger.debug(f"Retrieving stats for target ID: {target_id}")
        target = db.query(ScanTarget).filter(ScanTarget.id == target_id).first()
        if not target:
            logger.warning(f"Target not found with ID: {target_id}")
            raise HTTPException(status_code=404, detail="Target not found")

        scan_jobs = db.query(ScanJob).filter(ScanJob.target_id == target_id).all()

        total_scans = len(scan_jobs)
        successful_scans = len([job for job in scan_jobs if job.status == 'completed'])
        failed_scans = len([job for job in scan_jobs if job.status == 'failed'])

        latest_scan = (
            db.query(ScanJob)
            .filter(ScanJob.target_id == target_id)
            .order_by(ScanJob.start_time.desc())
            .first()
        )

        return {
            "target": {
                "id": target.id,
                "name": target.name,
                "path": target.path,
                "scan_frequency": target.scan_frequency,
                "is_sensitive": target.is_sensitive,
            },
            "scan_stats": {
                "total_scans": total_scans,
                "successful_scans": successful_scans,
                "failed_scans": failed_scans,
                "success_rate": (successful_scans / total_scans * 100) if total_scans > 0 else 0
            },
            "latest_scan": {
                "status": latest_scan.status if latest_scan else None,
                "start_time": latest_scan.start_time if latest_scan else None,
                "end_time": latest_scan.end_time if latest_scan else None,
                "error_message": latest_scan.error_message if latest_scan else None
            } if latest_scan else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving target stats: {target_id}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
