# src/services/change_monitor.py

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import threading
import time

import win32file
import win32con
import win32event
import pywintypes
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from src.core.scanner import ShareGuardScanner
from src.scanner.group_resolver import GroupResolver
from src.db.database import get_db
from src.db.models.scan import ScanJob, ScanResult, AccessEntry, ScanTarget
from src.db.models.changes import PermissionChange
from src.db.models.alerts import Alert, AlertConfiguration
from src.db.models.enums import AlertType, AlertSeverity
from src.utils.logger import setup_logger

logger = setup_logger('change_monitor')

class ACLChangeMonitor:
    """
    Monitors file system ACL changes and detects both direct and indirect access changes.
    
    Features:
    - Real-time file system change detection using Windows APIs
    - Comparison of ACL states between scans
    - Group membership change detection
    - Alert generation for various change types
    """
    
    def __init__(self, db_session_factory=get_db):
        self.db_session_factory = db_session_factory
        self.scanner = ShareGuardScanner()
        self.group_resolver = GroupResolver()
        
        # Monitoring state
        self._monitoring = False
        self._monitor_threads = {}
        self._stop_events = {}
        
        # Change tracking
        self._pending_changes = {}
        self._last_scan_cache = {}
        
        # Configuration
        self.scan_delay = 5  # Seconds to wait after detecting changes before scanning
        self.group_check_interval = 30  # 30 seconds between group membership checks
        self.batch_size = 100  # Max changes to process at once
        
        logger.info("ACL Change Monitor initialized")

    async def start_monitoring(self, target_paths: List[str] = None) -> None:
        """Start monitoring specified paths or all active scan targets."""
        if self._monitoring:
            logger.warning("Change monitoring already active")
            return
            
        try:
            # Get paths to monitor
            if not target_paths:
                target_paths = await self._get_active_target_paths()
            
            if not target_paths:
                logger.warning("No paths to monitor")
                return
                
            self._monitoring = True
            logger.info(f"Starting ACL change monitoring for {len(target_paths)} paths")
            
            # Start file system monitoring for each path
            for path in target_paths:
                if Path(path).exists():
                    await self._start_path_monitoring(path)
                else:
                    logger.warning(f"Path does not exist: {path}")
            
            # Start group membership monitoring
            await self._start_group_monitoring()
            
            logger.info("ACL change monitoring started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {str(e)}", exc_info=True)
            await self.stop_monitoring()
            raise

    async def stop_monitoring(self) -> None:
        """Stop all monitoring activities."""
        if not self._monitoring:
            return
            
        logger.info("Stopping ACL change monitoring")
        self._monitoring = False
        
        # Signal all threads to stop
        for event in self._stop_events.values():
            event.set()
        
        # Wait for threads to finish
        for thread in self._monitor_threads.values():
            if thread.is_alive():
                thread.join(timeout=5.0)
        
        self._monitor_threads.clear()
        self._stop_events.clear()
        
        logger.info("ACL change monitoring stopped")

    async def _get_active_target_paths(self) -> List[str]:
        """Get paths from active scan targets."""
        try:
            with next(self.db_session_factory()) as db:
                targets = db.query(ScanTarget).filter(
                    ScanTarget.scan_frequency != 'disabled'
                ).all()
                return [target.path for target in targets]
        except Exception as e:
            logger.error(f"Failed to get active target paths: {str(e)}")
            return []

    async def _start_path_monitoring(self, path: str) -> None:
        """Start monitoring a specific path for file system changes."""
        try:
            stop_event = threading.Event()
            self._stop_events[path] = stop_event
            
            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self._monitor_path_changes,
                args=(path, stop_event),
                daemon=True,
                name=f"ACLMonitor-{Path(path).name}"
            )
            
            self._monitor_threads[path] = monitor_thread
            monitor_thread.start()
            
            logger.info(f"Started monitoring path: {path}")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring for {path}: {str(e)}")

    def _monitor_path_changes(self, path: str, stop_event: threading.Event) -> None:
        """Monitor file system changes for a specific path using Windows APIs."""
        try:
            # Open directory handle for monitoring
            handle = win32file.CreateFile(
                path,
                win32file.FILE_LIST_DIRECTORY,
                win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_DELETE,
                None,
                win32file.OPEN_EXISTING,
                win32file.FILE_FLAG_BACKUP_SEMANTICS,
                None
            )
            
            # Monitoring flags for ACL changes
            flags = (
                win32con.FILE_NOTIFY_CHANGE_SECURITY |  # ACL changes
                win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |  # Attribute changes
                win32con.FILE_NOTIFY_CHANGE_DIR_NAME |  # Directory changes
                win32con.FILE_NOTIFY_CHANGE_FILE_NAME   # File changes
            )
            
            logger.info(f"File system monitoring active for: {path}")
            
            while not stop_event.is_set():
                try:
                    # Wait for changes with timeout
                    results = win32file.ReadDirectoryChangesW(
                        handle,
                        8192,  # Buffer size
                        True,  # Watch subtree
                        flags,
                        None,
                        None
                    )
                    
                    if results and not stop_event.is_set():
                        asyncio.run_coroutine_threadsafe(
                            self._process_file_changes(path, results),
                            asyncio.get_event_loop()
                        ).result()
                        
                except pywintypes.error as e:
                    if e.winerror == 995:  # Operation was aborted
                        break
                    logger.error(f"Windows API error monitoring {path}: {str(e)}")
                    time.sleep(5)  # Brief pause before retry
                    
                except Exception as e:
                    logger.error(f"Error monitoring {path}: {str(e)}")
                    time.sleep(5)
                    
        except Exception as e:
            logger.error(f"Failed to initialize monitoring for {path}: {str(e)}")
        finally:
            try:
                if 'handle' in locals():
                    win32file.CloseHandle(handle)
            except:
                pass
            logger.info(f"Stopped monitoring path: {path}")

    async def _process_file_changes(self, base_path: str, changes: List) -> None:
        """Process detected file system changes."""
        try:
            current_time = datetime.utcnow()
            change_paths = set()
            
            for action, filename in changes:
                full_path = str(Path(base_path) / filename)
                change_paths.add(full_path)
                
                # Log the change type
                action_name = {
                    1: "FILE_ACTION_ADDED",
                    2: "FILE_ACTION_REMOVED", 
                    3: "FILE_ACTION_MODIFIED",
                    4: "FILE_ACTION_RENAMED_OLD_NAME",
                    5: "FILE_ACTION_RENAMED_NEW_NAME"
                }.get(action, f"UNKNOWN_ACTION_{action}")
                
                logger.debug(f"Detected change: {action_name} - {full_path}")
            
            if change_paths:
                # Batch changes and schedule delayed scan
                await self._schedule_delayed_scan(base_path, change_paths, current_time)
                
        except Exception as e:
            logger.error(f"Error processing file changes: {str(e)}", exc_info=True)

    async def _schedule_delayed_scan(self, base_path: str, change_paths: Set[str], 
                                   change_time: datetime) -> None:
        """Schedule a delayed scan after detecting changes to batch them."""
        try:
            # Add to pending changes
            if base_path not in self._pending_changes:
                self._pending_changes[base_path] = {
                    'paths': set(),
                    'first_change': change_time,
                    'last_change': change_time,
                    'scheduled': False
                }
            
            pending = self._pending_changes[base_path]
            pending['paths'].update(change_paths)
            pending['last_change'] = change_time
            
            # Schedule scan if not already scheduled
            if not pending['scheduled']:
                pending['scheduled'] = True
                
                # Use asyncio.create_task for proper async scheduling
                asyncio.create_task(
                    self._delayed_scan_task(base_path, self.scan_delay)
                )
                
                logger.info(f"Scheduled delayed scan for {base_path} in {self.scan_delay} seconds")
                
        except Exception as e:
            logger.error(f"Error scheduling delayed scan: {str(e)}")

    async def _delayed_scan_task(self, base_path: str, delay: int) -> None:
        """Execute delayed scan after waiting for batch period."""
        try:
            await asyncio.sleep(delay)
            
            if base_path in self._pending_changes:
                pending = self._pending_changes[base_path]
                change_paths = pending['paths'].copy()
                
                # Clear pending changes
                del self._pending_changes[base_path]
                
                logger.info(f"Executing delayed scan for {base_path} "
                           f"({len(change_paths)} changed paths)")
                
                # Execute the change detection scan
                await self._execute_change_detection_scan(base_path, change_paths)
                
        except Exception as e:
            logger.error(f"Error in delayed scan task: {str(e)}", exc_info=True)

    async def _execute_change_detection_scan(self, base_path: str, 
                                           change_paths: Set[str]) -> None:
        """Execute a targeted scan to detect ACL changes."""
        try:
            # Get scan target for this path
            with next(self.db_session_factory()) as db:
                target = db.query(ScanTarget).filter(
                    ScanTarget.path == base_path
                ).first()
                
                if not target:
                    logger.warning(f"No scan target found for path: {base_path}")
                    return
                
                logger.info(f"Executing change detection scan for {base_path} with {len(change_paths)} changed paths")
                
                # Create new scan job for change detection
                scan_job = ScanJob(
                    target_id=target.id,
                    scan_type="change_detection",
                    status="running",
                    parameters={
                        "trigger": "file_system_change",
                        "changed_paths": list(change_paths),
                        "change_count": len(change_paths)
                    }
                )
                
                db.add(scan_job)
                db.commit()
                
                logger.info(f"Created change detection scan job {scan_job.id}")
                
                try:
                    # Execute the scan
                    scan_results = await self._perform_targeted_scan(
                        target, change_paths, scan_job.id
                    )
                    
                    # Save scan results to database
                    if scan_results:
                        logger.info(f"Saving {len(scan_results)} scan results to database")
                        for result in scan_results:
                            # Create ScanResult record
                            scan_result = ScanResult(
                                job_id=scan_job.id,
                                path=result['path'],
                                scan_time=result['scan_time'],
                                permissions=result.get('permissions', {}),
                                has_explicit_permissions=result.get('has_explicit_permissions', False),
                                inheritance_enabled=result.get('inheritance_enabled', True),
                                owner=result.get('owner', 'Unknown')
                            )
                            db.add(scan_result)
                            db.flush()  # Get the ID
                            
                            # Create AccessEntry records from aces
                            for ace in result.get('aces', []):
                                trustee = ace.get('trustee', {})
                                
                                access_entry = AccessEntry(
                                    scan_result_id=scan_result.id,
                                    trustee_name=trustee.get('name', ''),
                                    trustee_domain=trustee.get('domain', ''),
                                    trustee_sid=trustee.get('sid', ''),
                                    access_type=ace.get('type', 'Allow'),
                                    inherited=ace.get('inherited', False),
                                    permissions=ace.get('permissions', {})
                                )
                                db.add(access_entry)
                        
                        db.commit()
                        logger.info(f"Saved scan results for job {scan_job.id}")
                    
                    # Compare with previous scan results
                    changes_detected = await self._detect_permission_changes(
                        target, scan_results, scan_job.id
                    )
                    
                    # Update scan job status
                    scan_job.status = "completed"
                    scan_job.end_time = datetime.utcnow()
                    db.commit()
                    
                    logger.info(f"Change detection scan completed. "
                               f"Found {len(changes_detected)} permission changes")
                    
                    # Process alerts
                    if changes_detected:
                        await self._process_change_alerts(changes_detected, scan_job.id)
                    
                except Exception as scan_error:
                    scan_job.status = "failed"
                    scan_job.error_message = str(scan_error)
                    scan_job.end_time = datetime.utcnow()
                    db.commit()
                    raise
                    
        except Exception as e:
            logger.error(f"Error executing change detection scan: {str(e)}", exc_info=True)

    async def _perform_targeted_scan(self, target: ScanTarget, 
                                   change_paths: Set[str], job_id: int) -> List[Dict]:
        """Perform a targeted scan of changed paths."""
        try:
            scan_results = []
            
            # Scan each changed path
            for path in change_paths:
                if Path(path).exists():
                    try:
                        # Use the scanner to get current permissions
                        result = await asyncio.get_event_loop().run_in_executor(
                            None, 
                            self.scanner.scan_path,
                            path
                        )
                        
                        if result:
                            result['scan_job_id'] = job_id
                            result['scan_time'] = datetime.utcnow()
                            scan_results.append(result)
                            
                    except Exception as path_error:
                        logger.warning(f"Failed to scan {path}: {str(path_error)}")
                        
            return scan_results
            
        except Exception as e:
            logger.error(f"Error performing targeted scan: {str(e)}")
            return []

    async def _detect_permission_changes(self, target: ScanTarget, 
                                       current_results: List[Dict], 
                                       job_id: int) -> List[PermissionChange]:
        """Compare current scan results with previous results to detect changes."""
        try:
            changes_detected = []
            
            with next(self.db_session_factory()) as db:
                # Get the most recent completed scan for this target
                previous_job = db.query(ScanJob).filter(
                    and_(
                        ScanJob.target_id == target.id,
                        ScanJob.status == "completed",
                        ScanJob.id != job_id
                    )
                ).order_by(desc(ScanJob.end_time)).first()
                
                if not previous_job:
                    logger.info("No previous scan found for comparison")
                    return changes_detected
                
                # Get previous scan results
                previous_results = db.query(ScanResult).filter(
                    ScanResult.job_id == previous_job.id
                ).all()
                
                # Build lookup of previous results by path
                previous_by_path = {}
                for result in previous_results:
                    if result.path not in previous_by_path:
                        previous_by_path[result.path] = []
                    
                    # Get access entries for this result
                    access_entries = db.query(AccessEntry).filter(
                        AccessEntry.scan_result_id == result.id
                    ).all()
                    
                    previous_by_path[result.path] = [
                        {
                            'trustee_name': entry.trustee_name,
                            'trustee_domain': entry.trustee_domain,
                            'trustee_sid': entry.trustee_sid,
                            'access_type': entry.access_type,
                            'inherited': entry.inherited,
                            'permissions': entry.permissions
                        }
                        for entry in access_entries
                    ]
                
                # Compare current results with previous
                for current_result in current_results:
                    path = current_result['path']
                    current_aces = current_result.get('aces', [])
                    
                    logger.debug(f"Comparing permissions for path: {path}")
                    logger.debug(f"Current result has {len(current_aces)} ACEs")
                    
                    if path in previous_by_path:
                        previous_permissions = previous_by_path[path]
                        
                        # Convert current aces to comparable format
                        current_permissions = self._convert_aces_to_comparable_format(current_aces)
                        
                        # Detect changes in this path's permissions
                        path_changes = self._compare_path_permissions(
                            path, previous_permissions, current_permissions, job_id
                        )
                        if path_changes:
                            logger.info(f"Detected {len(path_changes)} permission changes for {path}")
                        changes_detected.extend(path_changes)
                    else:
                        # New path - all permissions are new
                        logger.info(f"New path detected: {path}")
                        current_permissions = self._convert_aces_to_comparable_format(current_aces)
                        new_change = PermissionChange(
                            scan_job_id=job_id,
                            change_type="new_path",
                            previous_state=None,
                            current_state=current_permissions,
                            detected_time=datetime.utcnow()
                        )
                        db.add(new_change)
                        changes_detected.append(new_change)
                
                db.commit()
                
            return changes_detected
            
        except Exception as e:
            logger.error(f"Error detecting permission changes: {str(e)}", exc_info=True)
            return []

    def _convert_aces_to_comparable_format(self, aces: List[Dict]) -> Dict:
        """Convert ACEs list to a format comparable with database entries."""
        comparable = {}
        for ace in aces:
            trustee = ace.get('trustee', {})
            if trustee:
                domain = trustee.get('domain', '')
                name = trustee.get('name', '')
                full_name = f"{domain}\\{name}" if domain else name
                
                comparable[full_name] = {
                    'trustee_name': name,
                    'trustee_domain': domain,
                    'trustee_sid': trustee.get('sid', ''),
                    'access_type': ace.get('type', 'Allow'),
                    'inherited': ace.get('inherited', False),
                    'permissions': ace.get('permissions', {})
                }
        return comparable

    def _compare_path_permissions(self, path: str, previous: List[Dict], 
                                current: Dict, job_id: int) -> List[PermissionChange]:
        """Compare permissions for a specific path."""
        changes = []
        
        try:
            logger.debug(f"Comparing path {path}: {len(previous)} previous entries vs {len(current)} current entries")
            
            # Build lookup maps - current is already in the right format
            previous_map = {
                f"{entry['trustee_domain']}\\{entry['trustee_name']}": entry 
                for entry in previous
            }
            current_map = current  # Current is already a dict with full_name as key
            
            # Find added permissions
            for trustee, current_entry in current_map.items():
                logger.debug(f"Checking if trustee {trustee} exists in previous permissions")
                if trustee not in previous_map:
                    logger.info(f"NEW ACCESS DETECTED: {trustee} added to {path}")
                    change = PermissionChange(
                        scan_job_id=job_id,
                        change_type="permission_added",
                        previous_state=None,
                        current_state={
                            'path': path,
                            'trustee': trustee,
                            'permissions': current_entry['permissions']
                        },
                        detected_time=datetime.utcnow()
                    )
                    # Save to database immediately
                    with next(self.db_session_factory()) as db:
                        db.add(change)
                        db.commit()
                        db.refresh(change)
                    changes.append(change)
                    logger.info(f"Added permission change to DB: {trustee} added to {path}")
                else:
                    logger.debug(f"Trustee {trustee} already exists in previous permissions")
            
            # Find removed permissions
            for trustee, previous_entry in previous_map.items():
                if trustee not in current_map:
                    change = PermissionChange(
                        scan_job_id=job_id,
                        change_type="permission_removed",
                        previous_state={
                            'path': path,
                            'trustee': trustee,
                            'permissions': previous_entry['permissions']
                        },
                        current_state=None,
                        detected_time=datetime.utcnow()
                    )
                    # Save to database immediately
                    with next(self.db_session_factory()) as db:
                        db.add(change)
                        db.commit()
                        db.refresh(change)
                    changes.append(change)
                    logger.info(f"Added permission change to DB: {trustee} removed from {path}")
            
            # Find modified permissions
            for trustee in set(previous_map.keys()) & set(current_map.keys()):
                prev_perms = previous_map[trustee]['permissions']
                curr_perms = current_map[trustee]['permissions']
                
                if prev_perms != curr_perms:
                    change = PermissionChange(
                        scan_job_id=job_id,
                        change_type="permission_modified",
                        previous_state={
                            'path': path,
                            'trustee': trustee,
                            'permissions': prev_perms
                        },
                        current_state={
                            'path': path,
                            'trustee': trustee,
                            'permissions': curr_perms
                        },
                        detected_time=datetime.utcnow()
                    )
                    # Save to database immediately
                    with next(self.db_session_factory()) as db:
                        db.add(change)
                        db.commit()
                        db.refresh(change)
                    changes.append(change)
                    logger.info(f"Added permission change to DB: {trustee} permissions modified on {path}")
                    
        except Exception as e:
            logger.error(f"Error comparing permissions for {path}: {str(e)}")
            
        return changes

    async def _start_group_monitoring(self) -> None:
        """Start monitoring group membership changes."""
        try:
            stop_event = threading.Event()
            self._stop_events['group_monitor'] = stop_event
            
            monitor_thread = threading.Thread(
                target=self._monitor_group_changes,
                args=(stop_event,),
                daemon=True,
                name="GroupMembershipMonitor"
            )
            
            self._monitor_threads['group_monitor'] = monitor_thread
            monitor_thread.start()
            
            logger.info("Started group membership monitoring")
            
        except Exception as e:
            logger.error(f"Failed to start group monitoring: {str(e)}")

    def _monitor_group_changes(self, stop_event: threading.Event) -> None:
        """Monitor group membership changes periodically."""
        try:
            logger.info("Group membership monitoring active")
            
            while not stop_event.is_set():
                try:
                    # Wait for check interval or stop signal
                    if stop_event.wait(self.group_check_interval):
                        break  # Stop event was set
                    
                    # Check for group membership changes
                    asyncio.run_coroutine_threadsafe(
                        self._check_group_membership_changes(),
                        asyncio.get_event_loop()
                    ).result()
                    
                except Exception as e:
                    logger.error(f"Error in group monitoring cycle: {str(e)}")
                    time.sleep(60)  # Wait before retry
                    
        except Exception as e:
            logger.error(f"Group monitoring thread error: {str(e)}")
        finally:
            logger.info("Group membership monitoring stopped")

    async def _check_group_membership_changes(self) -> None:
        """Check for changes in group memberships that affect access."""
        try:
            with next(self.db_session_factory()) as db:
                # Get all groups that have been granted access to monitored paths
                recent_scans = db.query(ScanJob).filter(
                    and_(
                        ScanJob.status == "completed",
                        ScanJob.end_time >= datetime.utcnow() - timedelta(days=7)
                    )
                ).limit(50).all()
                
                groups_to_check = set()
                
                for scan_job in recent_scans:
                    # Get access entries for groups
                    access_entries = db.query(AccessEntry).join(
                        ScanResult
                    ).filter(
                        ScanResult.job_id == scan_job.id
                    ).all()
                    
                    for entry in access_entries:
                        # Check if this is a group (not a user)
                        if entry.trustee_name and not entry.trustee_name.endswith('$'):
                            # Use group resolver to check if it's actually a group
                            try:
                                account_details = self.group_resolver._get_account_details(
                                    entry.trustee_name, 
                                    entry.trustee_domain or 'localhost'
                                )
                                if account_details['type'] in ['Group', 'WellKnownGroup', 'Alias']:
                                    groups_to_check.add(
                                        f"{entry.trustee_domain}\\{entry.trustee_name}"
                                    )
                            except Exception:
                                pass  # Skip if we can't determine type
                
                logger.info(f"Checking membership changes for {len(groups_to_check)} groups")
                
                # Check each group for membership changes
                for full_group_name in list(groups_to_check)[:20]:  # Limit batch size
                    try:
                        if '\\' in full_group_name:
                            domain, group_name = full_group_name.split('\\', 1)
                        else:
                            domain, group_name = 'localhost', full_group_name
                            
                        await self._check_single_group_changes(group_name, domain)
                        
                    except Exception as group_error:
                        logger.warning(f"Error checking group {full_group_name}: {str(group_error)}")
                        
        except Exception as e:
            logger.error(f"Error checking group membership changes: {str(e)}", exc_info=True)

    async def _check_single_group_changes(self, group_name: str, domain: str) -> None:
        """Check for membership changes in a single group."""
        try:
            # Get current group members
            current_members = await asyncio.get_event_loop().run_in_executor(
                None,
                self.group_resolver.get_group_members,
                group_name,
                domain,
                True  # Include nested groups
            )
            
            # Compare with cached previous state
            cache_key = f"{domain}\\{group_name}"
            previous_members = self._last_scan_cache.get(cache_key)
            
            if previous_members is None:
                # First time checking this group - just cache current state
                self._last_scan_cache[cache_key] = current_members
                return
            
            # Compare member lists
            current_member_sids = {
                member.get('sid') for member in current_members.get('all_members', [])
                if member.get('sid')
            }
            previous_member_sids = {
                member.get('sid') for member in previous_members.get('all_members', [])
                if member.get('sid')
            }
            
            added_members = current_member_sids - previous_member_sids
            removed_members = previous_member_sids - current_member_sids
            
            if added_members or removed_members:
                logger.info(f"Group membership changes detected for {cache_key}: "
                           f"{len(added_members)} added, {len(removed_members)} removed")
                
                # Create change records and alerts
                await self._record_group_membership_changes(
                    group_name, domain, added_members, removed_members,
                    current_members, previous_members
                )
                
                # Update cache with current state
                self._last_scan_cache[cache_key] = current_members
                
        except Exception as e:
            logger.error(f"Error checking group {domain}\\{group_name}: {str(e)}")

    async def _record_group_membership_changes(self, group_name: str, domain: str,
                                             added_sids: Set[str], removed_sids: Set[str],
                                             current_members: Dict, previous_members: Dict) -> None:
        """Record group membership changes and generate alerts."""
        try:
            with next(self.db_session_factory()) as db:
                # Create a virtual scan job for group changes
                scan_job = ScanJob(
                    target_id=None,  # No specific target
                    scan_type="group_membership_check",
                    status="completed",
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                    parameters={
                        "group_name": group_name,
                        "domain": domain,
                        "added_count": len(added_sids),
                        "removed_count": len(removed_sids)
                    }
                )
                db.add(scan_job)
                db.flush()  # Get the ID
                
                changes_created = []
                
                # Record added members
                for sid in added_sids:
                    # Find member details
                    member_info = None
                    for member in current_members.get('all_members', []):
                        if member.get('sid') == sid:
                            member_info = member
                            break
                    
                    change = PermissionChange(
                        scan_job_id=scan_job.id,
                        change_type="group_member_added",
                        previous_state=None,
                        current_state={
                            "group": f"{domain}\\{group_name}",
                            "member_sid": sid,
                            "member_info": member_info
                        },
                        detected_time=datetime.utcnow()
                    )
                    db.add(change)
                    changes_created.append(change)
                
                # Record removed members  
                for sid in removed_sids:
                    # Find member details from previous state
                    member_info = None
                    for member in previous_members.get('all_members', []):
                        if member.get('sid') == sid:
                            member_info = member
                            break
                    
                    change = PermissionChange(
                        scan_job_id=scan_job.id,
                        change_type="group_member_removed",
                        previous_state={
                            "group": f"{domain}\\{group_name}",
                            "member_sid": sid,
                            "member_info": member_info
                        },
                        current_state=None,
                        detected_time=datetime.utcnow()
                    )
                    db.add(change)
                    changes_created.append(change)
                
                db.commit()
                
                # Generate alerts for these changes
                if changes_created:
                    await self._process_change_alerts(changes_created, scan_job.id)
                    
        except Exception as e:
            logger.error(f"Error recording group membership changes: {str(e)}", exc_info=True)

    async def _process_change_alerts(self, changes: List[PermissionChange], 
                                   scan_job_id: int) -> None:
        """Process changes and generate appropriate alerts."""
        try:
            with next(self.db_session_factory()) as db:
                # Get alert configurations
                alert_configs = db.query(AlertConfiguration).filter(
                    AlertConfiguration.is_active == True
                ).all()
                
                logger.info(f"Processing {len(changes)} changes against {len(alert_configs)} active alert configs")
                
                alerts_created = []
                
                for change in changes:
                    logger.debug(f"Processing change: type={change.change_type}, id={change.id}")
                    logger.debug(f"Change details - current_state: {change.current_state}")
                    logger.debug(f"Change details - previous_state: {change.previous_state}")
                    
                    for config in alert_configs:
                        try:
                            logger.debug(f"Checking against config: {config.name} (type={config.alert_type})")
                            
                            # Check if this change matches the alert configuration
                            if self._change_matches_alert_config(change, config):
                                logger.info(f"Change {change.id} matches config {config.name}")
                                
                                alert = Alert(
                                    config_id=config.id,
                                    scan_job_id=scan_job_id,
                                    permission_change_id=change.id,
                                    severity=config.severity,
                                    message=self._generate_alert_message(change, config),
                                    details={
                                        "change_type": change.change_type,
                                        "change_id": change.id,
                                        "previous_state": change.previous_state,
                                        "current_state": change.current_state,
                                        "detected_time": change.detected_time.isoformat()
                                    }
                                )
                                db.add(alert)
                                alerts_created.append(alert)
                                logger.info(f"Created alert: {alert.message} [severity={alert.severity}]")
                            else:
                                logger.debug(f"Change {change.id} does not match config {config.name}")
                                
                        except Exception as config_error:
                            logger.warning(f"Error processing alert config {config.id}: {str(config_error)}")
                
                db.commit()
                
                if alerts_created:
                    logger.info(f"Generated {len(alerts_created)} alerts for {len(changes)} changes")
                    
                    # Send notifications (placeholder for future implementation)
                    await self._send_alert_notifications(alerts_created)
                else:
                    logger.warning(f"No alerts generated for {len(changes)} changes")
                    
        except Exception as e:
            logger.error(f"Error processing change alerts: {str(e)}", exc_info=True)

    def _change_matches_alert_config(self, change: PermissionChange, 
                                   config: AlertConfiguration) -> bool:
        """Check if a change matches an alert configuration."""
        try:
            logger.debug(f"Matching change type '{change.change_type}' against config type '{config.alert_type}'")
            
            # Basic type matching
            if config.alert_type == AlertType.PERMISSION_CHANGE.value:
                matches = change.change_type in [
                    "permission_added", "permission_removed", "permission_modified"
                ]
                logger.debug(f"PERMISSION_CHANGE match: {matches}")
                return matches
            elif config.alert_type == AlertType.NEW_ACCESS.value:
                matches = change.change_type == "permission_added"
                logger.debug(f"NEW_ACCESS match: {matches} (change_type={change.change_type})")
                return matches
            elif config.alert_type == AlertType.GROUP_MEMBERSHIP_CHANGE.value:
                matches = change.change_type in [
                    "group_member_added", "group_member_removed"
                ]
                logger.debug(f"GROUP_MEMBERSHIP_CHANGE match: {matches}")
                return matches
            
            # Check additional conditions if specified
            if config.conditions:
                conditions = config.conditions
                
                # Path-based conditions
                if 'paths' in conditions:
                    change_path = None
                    if change.current_state and 'path' in change.current_state:
                        change_path = change.current_state['path']
                    elif change.previous_state and 'path' in change.previous_state:
                        change_path = change.previous_state['path']
                    
                    if change_path:
                        for pattern in conditions['paths']:
                            if pattern in change_path or Path(change_path).match(pattern):
                                return True
                    return False
                
                # Trustee-based conditions
                if 'trustees' in conditions:
                    change_trustee = None
                    if change.current_state and 'trustee' in change.current_state:
                        change_trustee = change.current_state['trustee']
                    elif change.previous_state and 'trustee' in change.previous_state:
                        change_trustee = change.previous_state['trustee']
                    
                    if change_trustee:
                        return any(trustee.lower() in change_trustee.lower() 
                                 for trustee in conditions['trustees'])
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error matching change to alert config: {str(e)}")
            return False

    def _generate_alert_message(self, change: PermissionChange, 
                              config: AlertConfiguration) -> str:
        """Generate a human-readable alert message."""
        try:
            change_type = change.change_type
            
            if change_type == "permission_added":
                trustee = change.current_state.get('trustee', 'Unknown')
                path = change.current_state.get('path', 'Unknown path')
                return f"New access granted to {trustee} on {path}"
                
            elif change_type == "permission_removed":
                trustee = change.previous_state.get('trustee', 'Unknown')
                path = change.previous_state.get('path', 'Unknown path')
                return f"Access removed for {trustee} on {path}"
                
            elif change_type == "permission_modified":
                trustee = change.current_state.get('trustee', 'Unknown')
                path = change.current_state.get('path', 'Unknown path')
                return f"Access permissions modified for {trustee} on {path}"
                
            elif change_type == "group_member_added":
                group = change.current_state.get('group', 'Unknown group')
                member_info = change.current_state.get('member_info', {})
                member_name = member_info.get('full_name', 'Unknown user')
                return f"User {member_name} added to group {group}"
                
            elif change_type == "group_member_removed":
                group = change.previous_state.get('group', 'Unknown group')
                member_info = change.previous_state.get('member_info', {})
                member_name = member_info.get('full_name', 'Unknown user')
                return f"User {member_name} removed from group {group}"
                
            else:
                return f"Permission change detected: {change_type}"
                
        except Exception as e:
            logger.warning(f"Error generating alert message: {str(e)}")
            return f"Permission change detected: {change.change_type}"

    async def _send_alert_notifications(self, alerts: List[Alert]) -> None:
        """Send notifications for generated alerts (placeholder for future implementation)."""
        try:
            # This is a placeholder for notification delivery
            # Future implementations could include:
            # - Email notifications
            # - Webhook calls
            # - WebSocket messages to connected clients
            # - Integration with external alerting systems
            
            for alert in alerts:
                logger.info(f"ALERT [{alert.severity}]: {alert.message}")
                
        except Exception as e:
            logger.error(f"Error sending alert notifications: {str(e)}")

    async def get_recent_changes(self, hours: int = 24, 
                               change_types: List[str] = None) -> List[Dict]:
        """Get recent permission changes for API consumption."""
        try:
            with next(self.db_session_factory()) as db:
                query = db.query(PermissionChange).filter(
                    PermissionChange.detected_time >= datetime.utcnow() - timedelta(hours=hours)
                )
                
                if change_types:
                    query = query.filter(PermissionChange.change_type.in_(change_types))
                
                changes = query.order_by(desc(PermissionChange.detected_time)).limit(100).all()
                
                return [
                    {
                        "id": change.id,
                        "change_type": change.change_type,
                        "detected_time": change.detected_time.isoformat(),
                        "previous_state": change.previous_state,
                        "current_state": change.current_state,
                        "scan_job_id": change.scan_job_id
                    }
                    for change in changes
                ]
                
        except Exception as e:
            logger.error(f"Error getting recent changes: {str(e)}")
            return []

    async def get_active_alerts(self, acknowledged: bool = False) -> List[Dict]:
        """Get active alerts for API consumption."""
        try:
            with next(self.db_session_factory()) as db:
                query = db.query(Alert)
                
                if not acknowledged:
                    query = query.filter(Alert.acknowledged_at.is_(None))
                
                alerts = query.order_by(desc(Alert.created_at)).limit(50).all()
                
                return [
                    {
                        "id": alert.id,
                        "severity": alert.severity,
                        "message": alert.message,
                        "details": alert.details,
                        "created_at": alert.created_at.isoformat(),
                        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                        "acknowledged_by": alert.acknowledged_by
                    }
                    for alert in alerts
                ]
                
        except Exception as e:
            logger.error(f"Error getting active alerts: {str(e)}")
            return []