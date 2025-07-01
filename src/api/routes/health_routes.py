# src/api/routes/health_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import csv
import io
import logging

from src.db.database import get_db
from src.db.models.health import Issue, HealthScan, HealthScoreHistory, IssueStatus
from src.core.health_analyzer import HealthAnalyzer
from src.api.middleware.auth import get_current_user
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize health_analyzer lazily to avoid import-time errors
_health_analyzer = None

def get_health_analyzer():
    """Get or create the health analyzer instance."""
    global _health_analyzer
    if _health_analyzer is None:
        try:
            _health_analyzer = HealthAnalyzer()
            logger.info("HealthAnalyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize HealthAnalyzer: {e}")
            raise HTTPException(status_code=500, detail=f"Health analyzer initialization failed: {str(e)}")
    return _health_analyzer


@router.get("/score")
async def get_health_score(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get the current health score and issue summary."""
    try:
        result = get_health_analyzer().get_health_score()
        # Check if there's an error in the result
        if 'error' in result:
            logger.warning(f"Health analyzer returned error: {result['error']}")
            # Still return 200 with the error info so frontend can handle gracefully
            return result
        return result
    except Exception as e:
        logger.error(f"Error getting health score: {str(e)}")
        # Return graceful error response instead of 500
        return {
            'score': 0,
            'issues': {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'last_scan': None,
            'error': 'Service temporarily unavailable'
        }


@router.get("/issues")
async def get_issues(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    issue_type: Optional[str] = Query(None, description="Filter by issue type"),
    path_filter: Optional[str] = Query(None, description="Filter by path substring"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get paginated list of security issues."""
    try:
        # Validate parameters first
        if severity:
            valid_severities = ['low', 'medium', 'high', 'critical']
            if ',' in severity:
                severities = [s.strip() for s in severity.split(',')]
                for sev in severities:
                    if sev not in valid_severities:
                        raise HTTPException(status_code=400, detail=f"Invalid severity value: {sev}")
            elif severity not in valid_severities:
                raise HTTPException(status_code=400, detail="Invalid severity value")
            
        if issue_type:
            valid_types = [
                'broken_inheritance', 'direct_user_ace', 'orphaned_sid',
                'excessive_ace_count', 'conflicting_deny_order', 'over_permissive_groups'
            ]
            if ',' in issue_type:
                issue_types = [t.strip() for t in issue_type.split(',')]
                for it in issue_types:
                    if it not in valid_types:
                        raise HTTPException(status_code=400, detail=f"Invalid issue type: {it}")
            elif issue_type not in valid_types:
                raise HTTPException(status_code=400, detail="Invalid issue type")
        
        # Try database query with better error handling
        try:
            # Test database connection first
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            
            query = db.query(Issue).filter(Issue.status == IssueStatus.ACTIVE)
            
            # Apply filters
            if severity:
                # Handle multiple severities separated by comma
                if ',' in severity:
                    severities = [s.strip() for s in severity.split(',')]
                    query = query.filter(Issue.severity.in_(severities))
                else:
                    query = query.filter(Issue.severity == severity)
            
            if issue_type:
                # Handle multiple issue types separated by comma
                if ',' in issue_type:
                    issue_types = [t.strip() for t in issue_type.split(',')]
                    query = query.filter(Issue.issue_type.in_(issue_types))
                else:
                    query = query.filter(Issue.issue_type == issue_type)
            
            if path_filter:
                query = query.filter(Issue.path.contains(path_filter))
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    Issue.title.contains(search) | Issue.description.contains(search)
                )
            
            # Get total count
            total = query.count()
            
            # Get paginated results
            issues = (query
                     .order_by(Issue.severity.desc(), Issue.last_seen.desc())
                     .offset(skip)
                     .limit(limit)
                     .all())
            
            # Format response
            issues_data = []
            for issue in issues:
                issues_data.append({
                    'id': issue.id,
                    'type': issue.issue_type.value,
                    'severity': issue.severity.value,
                    'status': issue.status.value,
                    'path': issue.path,
                    'title': issue.title,
                    'description': issue.description,
                    'risk_score': issue.risk_score,
                    'first_detected': issue.first_detected.isoformat(),
                    'last_seen': issue.last_seen.isoformat(),
                    'affected_principals': issue.affected_principals or [],
                    'recommendations': issue.recommendations,
                    'impact_description': issue.impact_description,
                    'acl_details': issue.acl_details
                })
            
            return {
                'total': total,
                'issues': issues_data,
                'skip': skip,
                'limit': limit
            }
            
        except Exception as db_error:
            logger.error(f"Database error in get_issues: {str(db_error)}")
            # Return empty result with error info instead of 500
            return {
                'total': 0,
                'issues': [],
                'skip': skip,
                'limit': limit,
                'error': 'Health issues data not available - database not initialized'
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting issues: {str(e)}")
        # Return graceful error response instead of 500
        return {
            'total': 0,
            'issues': [],
            'skip': skip,
            'limit': limit,
            'error': 'Service temporarily unavailable'
        }


@router.get("/issues/{issue_id}")
async def get_issue_details(
    issue_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed information about a specific issue."""
    try:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        return {
            'id': issue.id,
            'type': issue.issue_type.value,
            'severity': issue.severity.value,
            'status': issue.status.value,
            'path': issue.path,
            'title': issue.title,
            'description': issue.description,
            'risk_score': issue.risk_score,
            'impact_description': issue.impact_description,
            'first_detected': issue.first_detected.isoformat(),
            'last_seen': issue.last_seen.isoformat(),
            'resolved_at': issue.resolved_at.isoformat() if issue.resolved_at else None,
            'affected_principals': issue.affected_principals or [],
            'recommendations': issue.recommendations,
            'acl_details': issue.acl_details or {},
            'context_data': issue.context_data or {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting issue details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve issue details")


@router.post("/scan")
async def trigger_health_scan(
    background_tasks: BackgroundTasks,
    target_paths: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Trigger a new health analysis scan."""
    try:
        # If no target paths provided, scan all available paths
        if not target_paths:
            target_paths = []
            
            # Get unique paths from existing scan results
            from src.db.models import ScanResult, ScanTarget
            try:
                # Test database connection first
                from sqlalchemy import text
                db.execute(text("SELECT 1"))
                
                # Get all scan result paths
                existing_paths = db.query(ScanResult.path).distinct().all()
                scan_result_paths = [path[0] for path in existing_paths] if existing_paths else []
                logger.info(f"Found {len(scan_result_paths)} paths with scan results")
                
                # Get all active scan target paths
                active_targets = db.query(ScanTarget).filter(ScanTarget.scan_frequency != 'disabled').all()
                target_paths_from_targets = [target.path for target in active_targets] if active_targets else []
                logger.info(f"Found {len(target_paths_from_targets)} active scan targets")
                
                # Combine both sources and remove duplicates
                all_paths = list(set(scan_result_paths + target_paths_from_targets))
                target_paths = all_paths
                
                logger.info(f"Scan result paths: {scan_result_paths}")
                logger.info(f"Target paths from targets: {target_paths_from_targets}")
                logger.info(f"Total unique paths to analyze: {len(target_paths)} - {target_paths}")
                
                if not target_paths:
                    return {
                        'message': 'No scan data or targets available. Please run a permission scan first from the Targets page.',
                        'status': 'no_data'
                    }
                    
            except Exception as db_error:
                logger.error(f"Database error when querying paths: {str(db_error)}")
                return {
                    'message': 'Database connection failed. Please check the database configuration.',
                    'status': 'database_error'
                }
        
        # Ensure we have target paths to process
        if not target_paths:
            logger.warning("No target paths found for health scan")
            return {
                'message': 'No target paths available for scanning. Please run a permission scan first.',
                'status': 'no_data'
            }
        
        # Validate paths (basic validation)
        for path in target_paths:
            if not path or len(path.strip()) == 0:
                raise HTTPException(status_code=400, detail="Invalid path provided")
        
        # Initialize health analyzer first to catch any initialization errors
        # before starting the background task
        try:
            health_analyzer = get_health_analyzer()
            logger.info("Health analyzer validated successfully")
        except Exception as e:
            logger.error(f"Failed to initialize health analyzer: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Health analyzer initialization failed: {str(e)}")
        
        # Start background scan
        def run_scan():
            try:
                logger.info(f"Starting background health scan with {len(target_paths)} paths")
                scan_id = health_analyzer.run_health_scan(target_paths)
                logger.info(f"Health scan {scan_id} completed successfully")
            except Exception as e:
                logger.error(f"Background health scan failed: {str(e)}", exc_info=True)
        
        background_tasks.add_task(run_scan)
        
        return {
            'message': 'Health scan started',
            'target_paths': target_paths,
            'status': 'running'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting health scan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start health scan: {str(e)}")


@router.get("/scans")
async def get_health_scans(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get list of health scans."""
    try:
        total = db.query(HealthScan).count()
        scans = (db.query(HealthScan)
                .order_by(HealthScan.start_time.desc())
                .offset(skip)
                .limit(limit)
                .all())
        
        scans_data = []
        for scan in scans:
            scans_data.append({
                'id': scan.id,
                'start_time': scan.start_time.isoformat(),
                'end_time': scan.end_time.isoformat() if scan.end_time else None,
                'status': scan.status,
                'total_paths': scan.total_paths,
                'processed_paths': scan.processed_paths,
                'issues_found': scan.issues_found,
                'overall_score': scan.overall_score,
                'error_message': scan.error_message
            })
        
        return {
            'total': total,
            'scans': scans_data,
            'skip': skip,
            'limit': limit
        }
        
    except Exception as e:
        logger.error(f"Error getting health scans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health scans")


@router.get("/score/history")
async def get_score_history(
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get health score history."""
    try:
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        history = (db.query(HealthScoreHistory)
                  .filter(HealthScoreHistory.timestamp >= cutoff_date)
                  .order_by(HealthScoreHistory.timestamp.asc())
                  .all())
        
        history_data = []
        for record in history:
            history_data.append({
                'timestamp': record.timestamp.isoformat(),
                'score': record.score,
                'issue_count': record.issue_count,
                'issues_by_severity': {
                    'critical': record.critical_count,
                    'high': record.high_count,
                    'medium': record.medium_count,
                    'low': record.low_count
                }
            })
        
        return {
            'history': history_data,
            'period_days': days
        }
        
    except Exception as e:
        logger.error(f"Error getting score history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve score history")


@router.put("/issues/{issue_id}/status")
async def update_issue_status(
    issue_id: int,
    status: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update issue status (mark as resolved, ignored, etc.)."""
    try:
        if status not in ['active', 'resolved', 'ignored']:
            raise HTTPException(status_code=400, detail="Invalid status value")
        
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        old_status = issue.status.value
        issue.status = IssueStatus(status)
        
        if status == 'resolved':
            issue.resolved_at = datetime.utcnow()
        elif status == 'active':
            issue.resolved_at = None
        
        db.commit()
        
        return {
            'id': issue_id,
            'old_status': old_status,
            'new_status': status,
            'resolved_at': issue.resolved_at.isoformat() if issue.resolved_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating issue status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update issue status")


@router.get("/issues/export")
async def export_issues(
    format: str = Query("csv", description="Export format (csv)"),
    severity: Optional[str] = Query(None),
    issue_type: Optional[str] = Query(None),
    path_filter: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export issues to CSV format."""
    try:
        if format != "csv":
            raise HTTPException(status_code=400, detail="Only CSV format is currently supported")
        
        # Build query with same filters as get_issues
        query = db.query(Issue).filter(Issue.status == IssueStatus.ACTIVE)
        
        if severity:
            if ',' in severity:
                severities = [s.strip() for s in severity.split(',')]
                query = query.filter(Issue.severity.in_(severities))
            else:
                query = query.filter(Issue.severity == severity)
        if issue_type:
            if ',' in issue_type:
                issue_types = [t.strip() for t in issue_type.split(',')]
                query = query.filter(Issue.issue_type.in_(issue_types))
            else:
                query = query.filter(Issue.issue_type == issue_type)
        if path_filter:
            query = query.filter(Issue.path.contains(path_filter))
        
        issues = query.order_by(Issue.severity.desc(), Issue.last_seen.desc()).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Type', 'Severity', 'Status', 'Path', 'Title', 'Description',
            'Risk Score', 'First Detected', 'Last Seen', 'Affected Principals',
            'Recommendations'
        ])
        
        # Write data
        for issue in issues:
            principals = ', '.join(issue.affected_principals) if issue.affected_principals else ''
            writer.writerow([
                issue.id,
                issue.issue_type.value,
                issue.severity.value,
                issue.status.value,
                issue.path,
                issue.title,
                issue.description,
                issue.risk_score,
                issue.first_detected.isoformat(),
                issue.last_seen.isoformat(),
                principals,
                issue.recommendations or ''
            ])
        
        output.seek(0)
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"shareguard_issues_{timestamp}.csv"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting issues: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export issues")


@router.get("/debug/paths")
async def debug_scan_paths(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Debug endpoint to show what paths are available for health scanning."""
    try:
        from src.db.models import ScanResult, ScanTarget
        
        # Get scan result paths
        existing_paths = db.query(ScanResult.path, ScanResult.scan_time, ScanResult.success).all()
        scan_results_data = [
            {
                "path": path,
                "scan_time": scan_time.isoformat() if scan_time else None,
                "success": success
            }
            for path, scan_time, success in existing_paths
        ]
        
        # Get scan target paths
        active_targets = db.query(ScanTarget.path, ScanTarget.scan_frequency, ScanTarget.name).filter(
            ScanTarget.scan_frequency != 'disabled'
        ).all()
        scan_targets_data = [
            {
                "path": path,
                "scan_frequency": scan_frequency,
                "name": name
            }
            for path, scan_frequency, name in active_targets
        ]
        
        # Get all unique paths that would be scanned
        scan_result_paths = [row[0] for row in existing_paths if row[2]]  # only successful scans
        target_paths = [row[0] for row in active_targets]
        all_unique_paths = list(set(scan_result_paths + target_paths))
        
        return {
            "scan_results": scan_results_data,
            "scan_targets": scan_targets_data,
            "unique_paths_for_health_scan": all_unique_paths,
            "total_scan_results": len(scan_results_data),
            "total_active_targets": len(scan_targets_data),
            "total_unique_paths": len(all_unique_paths)
        }
        
    except Exception as e:
        logger.error(f"Error in debug paths: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")


@router.get("/debug/scan-data/{path:path}")
async def debug_scan_data(
    path: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Debug endpoint to show scan data for a specific path."""
    try:
        from src.db.models import ScanResult
        import json
        
        # Get the latest scan result for this path
        scan_result = db.query(ScanResult).filter(
            ScanResult.path == path
        ).order_by(ScanResult.scan_time.desc()).first()
        
        if not scan_result:
            # Try to scan the path now
            from src.core.scanner import ShareGuardScanner
            scanner = ShareGuardScanner()
            fresh_scan = scanner.scan_path(path)
            
            return {
                "path": path,
                "has_stored_scan": False,
                "fresh_scan_result": fresh_scan,
                "fresh_scan_success": fresh_scan.get('success', False)
            }
        
        # Parse the stored permissions data
        permissions_data = scan_result.permissions
        if isinstance(permissions_data, str):
            try:
                permissions_data = json.loads(permissions_data)
            except json.JSONDecodeError:
                permissions_data = {"error": "Invalid JSON in stored scan"}
        
        return {
            "path": path,
            "has_stored_scan": True,
            "scan_time": scan_result.scan_time.isoformat() if scan_result.scan_time else None,
            "success": scan_result.success,
            "permissions_data": permissions_data,
            "permissions_data_keys": list(permissions_data.keys()) if isinstance(permissions_data, dict) else None,
            "has_inheritance_enabled_field": "inheritance_enabled" in permissions_data if isinstance(permissions_data, dict) else False,
            "inheritance_enabled_value": permissions_data.get("inheritance_enabled") if isinstance(permissions_data, dict) else None,
            "aces_count": len(permissions_data.get("aces", [])) if isinstance(permissions_data, dict) else 0
        }
        
    except Exception as e:
        logger.error(f"Error in debug scan data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")


@router.post("/debug/fresh-scan")
async def debug_fresh_scan(
    path: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Debug endpoint to run a fresh scan and immediate health analysis on a single path."""
    try:
        from src.core.scanner import ShareGuardScanner
        from src.db.models import ScanResult
        import json
        
        scanner = ShareGuardScanner()
        
        # Run fresh scan
        logger.info(f"Running fresh scan on {path}")
        scan_result = scanner.scan_path(path)
        
        if not scan_result.get('success', False):
            return {
                "path": path,
                "scan_success": False,
                "scan_error": scan_result.get('error', 'Unknown scan error'),
                "scan_result": scan_result
            }
        
        # Store the scan result
        from datetime import timezone
        new_scan_result = ScanResult(
            path=path,
            scan_time=datetime.now(timezone.utc),
            success=True,
            permissions=scan_result,
            error_message=None
        )
        db.add(new_scan_result)
        db.commit()
        
        # Run health analysis on this single path
        health_analyzer = get_health_analyzer()
        path_issues = health_analyzer._analyze_path_results(path, scan_result, 0)
        significant_issues = health_analyzer._filter_significant_issues(path_issues)
        
        return {
            "path": path,
            "scan_success": True,
            "scan_result_keys": list(scan_result.keys()),
            "inheritance_enabled": scan_result.get('inheritance_enabled', 'NOT_FOUND'),
            "aces_count": len(scan_result.get('aces', [])),
            "permissions_structure": list(scan_result.get('permissions', {}).keys()) if 'permissions' in scan_result else None,
            "raw_issues_found": len(path_issues),
            "significant_issues_found": len(significant_issues),
            "issues_details": [
                {
                    "type": issue.get('issue_type', {}).value if hasattr(issue.get('issue_type', {}), 'value') else str(issue.get('issue_type')),
                    "severity": issue.get('severity', {}).value if hasattr(issue.get('severity', {}), 'value') else str(issue.get('severity')),
                    "title": issue.get('title'),
                    "risk_score": issue.get('risk_score')
                }
                for issue in significant_issues
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in debug fresh scan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Debug scan failed: {str(e)}")


@router.get("/stats")
async def get_health_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get overall health statistics."""
    try:
        # Get issue counts by severity
        active_issues = db.query(Issue).filter(Issue.status == IssueStatus.ACTIVE)
        
        severity_counts = {
            'critical': active_issues.filter(Issue.severity == 'critical').count(),
            'high': active_issues.filter(Issue.severity == 'high').count(),
            'medium': active_issues.filter(Issue.severity == 'medium').count(),
            'low': active_issues.filter(Issue.severity == 'low').count()
        }
        
        # Get issue counts by type
        type_counts = {}
        for issue_type in ['broken_inheritance', 'direct_user_ace', 'orphaned_sid',
                          'excessive_ace_count', 'conflicting_deny_order', 'over_permissive_groups']:
            type_counts[issue_type] = active_issues.filter(Issue.issue_type == issue_type).count()
        
        # Get latest score
        latest_score = db.query(HealthScoreHistory).order_by(HealthScoreHistory.timestamp.desc()).first()
        
        # Get scan statistics
        total_scans = db.query(HealthScan).count()
        successful_scans = db.query(HealthScan).filter(HealthScan.status == 'completed').count()
        
        return {
            'current_score': latest_score.score if latest_score else 0,
            'total_issues': sum(severity_counts.values()),
            'issues_by_severity': severity_counts,
            'issues_by_type': type_counts,
            'scan_statistics': {
                'total_scans': total_scans,
                'successful_scans': successful_scans,
                'success_rate': (successful_scans / total_scans * 100) if total_scans > 0 else 0
            },
            'last_scan': latest_score.timestamp.isoformat() if latest_score else None
        }
        
    except Exception as e:
        logger.error(f"Error getting health stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health statistics")