# src/api/routes/alert_routes.py

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import os

from src.db.database import get_db
from src.db.models.alerts import Alert, AlertConfiguration
from src.db.models.changes import PermissionChange
from src.db.models.scan import ScanJob, ScanTarget
from src.db.models.enums import AlertType, AlertSeverity
from src.services.notification_service import notification_service
from src.services.change_monitor import change_monitor
# from src.services.group_monitor import GroupMembershipTracker
from src.api.middleware.auth import get_current_user, get_current_service_account
from src.utils.logger import setup_logger
from pydantic import BaseModel
from enum import Enum

logger = setup_logger('alert_routes')

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Services are already initialized as global instances
# change_monitor is imported from src.services.change_monitor
# group_tracker = GroupMembershipTracker()

# Pydantic models for API
class AlertConfigurationCreate(BaseModel):
    target_id: Optional[int] = None
    name: str
    alert_type: str
    severity: str
    conditions: Optional[Dict[str, Any]] = None
    notifications: Optional[Dict[str, Any]] = None
    is_active: bool = True

class AlertConfigurationUpdate(BaseModel):
    name: Optional[str] = None
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    notifications: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class AlertAcknowledge(BaseModel):
    acknowledged_by: str
    notes: Optional[str] = None

class WebSocketFilters(BaseModel):
    types: Optional[List[str]] = None
    min_severity: Optional[str] = None
    paths: Optional[List[str]] = None

# Alert Configuration endpoints
@router.post("/configurations", response_model=Dict[str, Any])
async def create_alert_configuration(
    config: AlertConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new alert configuration."""
    try:
        # Validate alert type
        if config.alert_type not in [e.value for e in AlertType]:
            raise HTTPException(status_code=400, detail="Invalid alert type")
        
        # Validate severity
        if config.severity not in [e.value for e in AlertSeverity]:
            raise HTTPException(status_code=400, detail="Invalid severity level")
        
        # Validate target exists if specified
        if config.target_id:
            target = db.query(ScanTarget).filter(ScanTarget.id == config.target_id).first()
            if not target:
                raise HTTPException(status_code=404, detail="Scan target not found")
        
        # Create configuration
        db_config = AlertConfiguration(
            target_id=config.target_id,
            name=config.name,
            alert_type=config.alert_type,
            severity=config.severity,
            conditions=config.conditions,
            notifications=config.notifications,
            is_active=config.is_active
        )
        
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        
        logger.info(f"Created alert configuration {db_config.id}: {config.name}")
        
        return {
            "id": db_config.id,
            "target_id": db_config.target_id,
            "name": db_config.name,
            "alert_type": db_config.alert_type,
            "severity": db_config.severity,
            "conditions": db_config.conditions,
            "notifications": db_config.notifications,
            "is_active": db_config.is_active,
            "created_at": db_config.created_at.isoformat(),
            "updated_at": db_config.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create alert configuration")

@router.get("/configurations", response_model=List[Dict[str, Any]])
async def get_alert_configurations(
    target_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get alert configurations with optional filtering."""
    try:
        query = db.query(AlertConfiguration)
        
        if target_id is not None:
            query = query.filter(AlertConfiguration.target_id == target_id)
        
        if is_active is not None:
            query = query.filter(AlertConfiguration.is_active == is_active)
        
        configurations = query.order_by(desc(AlertConfiguration.created_at)).offset(skip).limit(limit).all()
        
        return [
            {
                "id": config.id,
                "target_id": config.target_id,
                "name": config.name,
                "alert_type": config.alert_type,
                "severity": config.severity,
                "conditions": config.conditions,
                "notifications": config.notifications,
                "is_active": config.is_active,
                "created_at": config.created_at.isoformat(),
                "updated_at": config.updated_at.isoformat(),
                "target_name": config.target.name if config.target else None
            }
            for config in configurations
        ]
        
    except Exception as e:
        logger.error(f"Error getting alert configurations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get alert configurations")

@router.get("/configurations/{config_id}", response_model=Dict[str, Any])
async def get_alert_configuration(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific alert configuration."""
    try:
        config = db.query(AlertConfiguration).filter(AlertConfiguration.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="Alert configuration not found")
        
        # Get alert statistics
        total_alerts = db.query(Alert).filter(Alert.config_id == config_id).count()
        recent_alerts = db.query(Alert).filter(
            and_(
                Alert.config_id == config_id,
                Alert.created_at >= datetime.utcnow() - timedelta(days=7)
            )
        ).count()
        
        return {
            "id": config.id,
            "target_id": config.target_id,
            "name": config.name,
            "alert_type": config.alert_type,
            "severity": config.severity,
            "conditions": config.conditions,
            "notifications": config.notifications,
            "is_active": config.is_active,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
            "target_name": config.target.name if config.target else None,
            "statistics": {
                "total_alerts": total_alerts,
                "recent_alerts": recent_alerts
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert configuration {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get alert configuration")

@router.put("/configurations/{config_id}", response_model=Dict[str, Any])
async def update_alert_configuration(
    config_id: int,
    config_update: AlertConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an alert configuration."""
    try:
        config = db.query(AlertConfiguration).filter(AlertConfiguration.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="Alert configuration not found")
        
        # Update fields
        update_data = config_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "alert_type" and value not in [e.value for e in AlertType]:
                raise HTTPException(status_code=400, detail="Invalid alert type")
            if field == "severity" and value not in [e.value for e in AlertSeverity]:
                raise HTTPException(status_code=400, detail="Invalid severity level")
            setattr(config, field, value)
        
        config.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(config)
        
        logger.info(f"Updated alert configuration {config_id}")
        
        return {
            "id": config.id,
            "target_id": config.target_id,
            "name": config.name,
            "alert_type": config.alert_type,
            "severity": config.severity,
            "conditions": config.conditions,
            "notifications": config.notifications,
            "is_active": config.is_active,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert configuration {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update alert configuration")

@router.delete("/configurations/{config_id}")
async def delete_alert_configuration(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an alert configuration."""
    try:
        config = db.query(AlertConfiguration).filter(AlertConfiguration.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="Alert configuration not found")
        
        db.delete(config)
        db.commit()
        
        logger.info(f"Deleted alert configuration {config_id}")
        
        return {"message": "Alert configuration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert configuration {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete alert configuration")

# Alert management endpoints
@router.get("/", response_model=List[Dict[str, Any]])
async def get_alerts(
    acknowledged: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None),
    hours: Optional[int] = Query(24, ge=1, le=8760),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get alerts with optional filtering."""
    try:
        query = db.query(Alert)
        
        # Apply filters
        if acknowledged is not None:
            if acknowledged:
                query = query.filter(Alert.acknowledged_at.isnot(None))
            else:
                query = query.filter(Alert.acknowledged_at.is_(None))
        
        if severity:
            query = query.filter(Alert.severity == severity)
        
        if alert_type:
            query = query.join(AlertConfiguration).filter(AlertConfiguration.alert_type == alert_type)
        
        if hours:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(Alert.created_at >= cutoff_time)
        
        alerts = query.order_by(desc(Alert.created_at)).offset(skip).limit(limit).all()
        
        return [
            {
                "id": alert.id,
                "config_id": alert.config_id,
                "scan_job_id": alert.scan_job_id,
                "permission_change_id": alert.permission_change_id,
                "severity": alert.severity,
                "message": alert.message,
                "details": alert.details,
                "created_at": alert.created_at.isoformat(),
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "acknowledged_by": alert.acknowledged_by,
                "configuration_name": alert.configuration.name if alert.configuration else None,
                "target_name": alert.configuration.target.name if alert.configuration and alert.configuration.target else None
            }
            for alert in alerts
        ]
        
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")

@router.get("/{alert_id}", response_model=Dict[str, Any])
async def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific alert with full details."""
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Get related permission change details
        permission_change = None
        if alert.permission_change_id:
            change = db.query(PermissionChange).filter(
                PermissionChange.id == alert.permission_change_id
            ).first()
            if change:
                permission_change = {
                    "id": change.id,
                    "change_type": change.change_type,
                    "previous_state": change.previous_state,
                    "current_state": change.current_state,
                    "detected_time": change.detected_time.isoformat()
                }
        
        return {
            "id": alert.id,
            "config_id": alert.config_id,
            "scan_job_id": alert.scan_job_id,
            "permission_change_id": alert.permission_change_id,
            "severity": alert.severity,
            "message": alert.message,
            "details": alert.details,
            "created_at": alert.created_at.isoformat(),
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            "acknowledged_by": alert.acknowledged_by,
            "configuration": {
                "id": alert.configuration.id,
                "name": alert.configuration.name,
                "alert_type": alert.configuration.alert_type,
                "conditions": alert.configuration.conditions
            } if alert.configuration else None,
            "permission_change": permission_change
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get alert")

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    acknowledge_data: AlertAcknowledge,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Acknowledge an alert."""
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        if alert.acknowledged_at:
            raise HTTPException(status_code=400, detail="Alert already acknowledged")
        
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledge_data.acknowledged_by
        
        # Add notes to details if provided
        if acknowledge_data.notes:
            if not alert.details:
                alert.details = {}
            alert.details['acknowledgment_notes'] = acknowledge_data.notes
        
        db.commit()
        
        logger.info(f"Alert {alert_id} acknowledged by {acknowledge_data.acknowledged_by}")
        
        return {"message": "Alert acknowledged successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")

# Statistics and dashboard endpoints
@router.get("/statistics/summary", response_model=Dict[str, Any])
async def get_alert_statistics(
    hours: int = Query(24, ge=1, le=8760),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get alert statistics for dashboard."""
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total alerts in time period
        total_alerts = db.query(Alert).filter(Alert.created_at >= cutoff_time).count()
        
        # Alerts by severity
        severity_counts = db.query(
            Alert.severity,
            func.count(Alert.id).label('count')
        ).filter(
            Alert.created_at >= cutoff_time
        ).group_by(Alert.severity).all()
        
        # Unacknowledged alerts
        unacknowledged = db.query(Alert).filter(
            and_(
                Alert.created_at >= cutoff_time,
                Alert.acknowledged_at.is_(None)
            )
        ).count()
        
        # Alerts by type
        type_counts = db.query(
            AlertConfiguration.alert_type,
            func.count(Alert.id).label('count')
        ).join(
            Alert, Alert.config_id == AlertConfiguration.id
        ).filter(
            Alert.created_at >= cutoff_time
        ).group_by(AlertConfiguration.alert_type).all()
        
        # Recent changes that triggered alerts
        recent_changes = db.query(PermissionChange).join(
            Alert, Alert.permission_change_id == PermissionChange.id
        ).filter(
            Alert.created_at >= cutoff_time
        ).order_by(desc(PermissionChange.detected_time)).limit(10).all()
        
        return {
            "time_period_hours": hours,
            "total_alerts": total_alerts,
            "unacknowledged_alerts": unacknowledged,
            "alerts_by_severity": {
                severity: count for severity, count in severity_counts
            },
            "alerts_by_type": {
                alert_type: count for alert_type, count in type_counts
            },
            "recent_changes": [
                {
                    "id": change.id,
                    "change_type": change.change_type,
                    "detected_time": change.detected_time.isoformat(),
                    "current_state": change.current_state,
                    "previous_state": change.previous_state
                }
                for change in recent_changes
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get alert statistics")

# Change monitoring endpoints
@router.get("/changes/recent", response_model=List[Dict[str, Any]])
async def get_recent_changes(
    hours: int = Query(24, ge=1, le=168),
    change_types: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get recent permission changes."""
    try:
        change_type_list = change_types.split(',') if change_types else None
        changes = await change_monitor.get_recent_changes(hours, change_type_list)
        
        # Apply pagination
        start_idx = skip
        end_idx = skip + limit
        paginated_changes = changes[start_idx:end_idx]
        
        return paginated_changes
        
    except Exception as e:
        logger.error(f"Error getting recent changes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recent changes")

@router.post("/monitoring/start")
async def start_monitoring(
    paths: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start ACL change monitoring."""
    try:
        # If no paths provided, get all active scan target paths
        if not paths:
            scan_targets = db.query(ScanTarget).all()
            paths = [target.path for target in scan_targets if target.path and os.path.exists(target.path)]
            logger.info(f"Auto-detected scan target paths: {paths}")
        
        await change_monitor.start_monitoring(paths)
        # await group_tracker.start_monitoring()
        
        logger.info(f"Started ACL monitoring on {len(paths)} paths")
        
        return {
            "message": "Change monitoring started successfully",
            "monitoring_paths": paths,
            "path_count": len(paths)
        }
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start monitoring")

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: dict = Depends(get_current_user)):
    """Stop ACL change monitoring."""
    try:
        await change_monitor.stop_monitoring()
        # await group_tracker.stop_monitoring()
        
        logger.info("Stopped ACL monitoring")
        
        return {"message": "Change monitoring stopped successfully"}
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop monitoring")

@router.get("/monitoring/status", response_model=Dict[str, Any])
async def get_monitoring_status(current_user: dict = Depends(get_current_user)):
    """Get current monitoring status."""
    try:
        # group_status = await group_tracker.get_monitoring_status()
        notification_stats = await notification_service.get_service_stats()
        
        return {
            "change_monitoring_active": change_monitor.is_monitoring,
            "monitored_paths": list(change_monitor.monitoring_paths),
            "notification_service_stats": notification_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring status")

@router.post("/test-notification")
async def send_test_notification(
    message: str = "Test notification",
    current_user: dict = Depends(get_current_user)
):
    """Send a test notification to all connected WebSocket clients."""
    try:
        from src.services.notification_service import Notification, NotificationType
        import uuid
        from datetime import datetime
        
        test_notification = Notification(
            id=str(uuid.uuid4()),
            type=NotificationType.SYSTEM_STATUS,
            title="Test Notification",
            message=message,
            severity="info",
            timestamp=datetime.utcnow().isoformat(),
            data={"test": True}
        )
        
        await notification_service.send_notification(test_notification, broadcast=True)
        
        return {
            "success": True,
            "message": "Test notification sent",
            "notification_id": test_notification.id
        }
        
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send test notification")

@router.get("/websocket-debug")
async def websocket_debug(current_user: dict = Depends(get_current_user)):
    """Debug WebSocket connection status."""
    try:
        stats = await notification_service.get_service_stats()
        return {
            "websocket_stats": stats,
            "notification_service_running": hasattr(notification_service, '_notification_task') and notification_service._notification_task is not None
        }
    except Exception as e:
        logger.error(f"Error getting WebSocket debug info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Test WebSocket endpoint
@router.websocket("/test")
async def test_websocket_endpoint(websocket: WebSocket):
    """Simple test WebSocket endpoint."""
    print("DEBUG: Test WebSocket endpoint called!")
    logger.info("=== TEST WEBSOCKET ENDPOINT CALLED ===")
    await websocket.accept()
    await websocket.send_text("Hello WebSocket!")
    await websocket.close()

# WebSocket endpoint for real-time notifications
@router.websocket("/notifications")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    filters: Optional[str] = Query(None),
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for real-time alert notifications."""
    logger.info(f"=== WEBSOCKET ENDPOINT CALLED === user: {user_id}, token: {token[:20] if token else 'None'}")
    print(f"DEBUG: WebSocket endpoint called - user: {user_id}, token: {token[:20] if token else 'None'}")
    logger.info(f"WebSocket connection attempt from user: {user_id}")
    try:
        # Simplified WebSocket authentication
        if not token:
            logger.warning("No token provided for WebSocket connection")
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        # Basic token validation without full auth middleware
        try:
            import jwt
            from config.settings import JWT_SECRET_KEY, JWT_ALGORITHM
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            username = payload.get("sub")
            if not username:
                raise ValueError("Invalid token payload")
            logger.info(f"WebSocket authentication successful for user: {username}")
        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {str(e)}")
            await websocket.close(code=1008, reason="Authentication failed")
            return
        
        # Parse filters if provided
        parsed_filters = None
        if filters:
            try:
                parsed_filters = json.loads(filters)
            except json.JSONDecodeError:
                logger.warning(f"Invalid filters JSON: {filters}")
        
        # Handle the WebSocket connection with authenticated user
        await notification_service.handle_websocket_connection(
            websocket, user_id or service_account.username, parsed_filters
        )
        
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close()
        except:
            pass