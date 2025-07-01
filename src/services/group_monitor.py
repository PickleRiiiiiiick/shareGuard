# src/services/group_monitor.py

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any
import threading
import time
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, distinct

from src.scanner.group_resolver import GroupResolver
from src.db.database import get_db
from src.db.models.scan import ScanJob, AccessEntry
from src.db.models.changes import PermissionChange
from src.utils.logger import setup_logger

logger = setup_logger('group_monitor')

class GroupMembershipTracker:
    """
    Enhanced group membership tracking service that monitors for indirect access changes.
    
    This service tracks:
    - Direct group membership changes
    - Nested group membership changes
    - Impact analysis of membership changes on file access
    - Historical group membership data
    """
    
    def __init__(self, db_session_factory=get_db):
        self.db_session_factory = db_session_factory
        self.group_resolver = GroupResolver()
        
        # Membership snapshots cache
        self._membership_snapshots = {}
        self._last_snapshot_time = {}
        
        # Configuration
        self.snapshot_interval = 3600  # 1 hour between snapshots
        self.change_detection_interval = 300  # 5 minutes between change checks
        self.max_snapshot_age = 86400 * 7  # Keep snapshots for 7 days
        
        # Monitoring state
        self._monitoring = False
        self._monitor_thread = None
        self._stop_event = threading.Event()
        
        logger.info("Group Membership Tracker initialized")

    async def start_monitoring(self) -> None:
        """Start continuous group membership monitoring."""
        if self._monitoring:
            logger.warning("Group membership monitoring already active")
            return
            
        try:
            self._monitoring = True
            self._stop_event.clear()
            
            # Start monitoring thread
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="GroupMembershipTracker"
            )
            self._monitor_thread.start()
            
            logger.info("Group membership monitoring started")
            
        except Exception as e:
            logger.error(f"Failed to start group membership monitoring: {str(e)}", exc_info=True)
            self._monitoring = False
            raise

    async def stop_monitoring(self) -> None:
        """Stop group membership monitoring."""
        if not self._monitoring:
            return
            
        logger.info("Stopping group membership monitoring")
        self._monitoring = False
        self._stop_event.set()
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=10.0)
        
        logger.info("Group membership monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop running in separate thread."""
        try:
            logger.info("Group membership monitoring loop started")
            
            while not self._stop_event.is_set():
                try:
                    # Run monitoring cycle
                    asyncio.run_coroutine_threadsafe(
                        self._run_monitoring_cycle(),
                        asyncio.get_event_loop()
                    ).result()
                    
                    # Wait for next cycle or stop signal
                    if self._stop_event.wait(self.change_detection_interval):
                        break
                        
                except Exception as e:
                    logger.error(f"Error in monitoring cycle: {str(e)}", exc_info=True)
                    time.sleep(60)  # Wait before retry
                    
        except Exception as e:
            logger.error(f"Group membership monitoring loop error: {str(e)}", exc_info=True)
        finally:
            logger.info("Group membership monitoring loop ended")

    async def _run_monitoring_cycle(self) -> None:
        """Run a single monitoring cycle."""
        try:
            # Get groups that need monitoring
            groups_to_monitor = await self._get_groups_to_monitor()
            
            if not groups_to_monitor:
                logger.debug("No groups to monitor")
                return
            
            logger.info(f"Monitoring {len(groups_to_monitor)} groups for membership changes")
            
            # Check each group for changes
            changes_detected = []
            for group_info in groups_to_monitor:
                try:
                    group_changes = await self._check_group_membership_changes(group_info)
                    if group_changes:
                        changes_detected.extend(group_changes)
                        
                except Exception as group_error:
                    logger.warning(f"Error checking group {group_info}: {str(group_error)}")
            
            if changes_detected:
                logger.info(f"Detected {len(changes_detected)} group membership changes")
                await self._process_membership_changes(changes_detected)
            
            # Clean up old snapshots
            await self._cleanup_old_snapshots()
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {str(e)}", exc_info=True)

    async def _get_groups_to_monitor(self) -> List[Dict[str, str]]:
        """Get list of groups that should be monitored based on recent access grants."""
        try:
            with next(self.db_session_factory()) as db:
                # Get groups that have been granted access in recent scans
                recent_cutoff = datetime.utcnow() - timedelta(days=30)
                
                # Query for access entries where trustee appears to be a group
                access_entries = db.query(AccessEntry).join(
                    ScanJob
                ).filter(
                    and_(
                        ScanJob.end_time >= recent_cutoff,
                        ScanJob.status == "completed"
                    )
                ).limit(1000).all()
                
                groups_found = set()
                
                for entry in access_entries:
                    if entry.trustee_name and entry.trustee_domain:
                        try:
                            # Use group resolver to check if this is actually a group
                            full_name = f"{entry.trustee_domain}\\{entry.trustee_name}"
                            
                            # Check cache first to avoid expensive lookups
                            if full_name not in self._membership_snapshots:
                                account_details = self.group_resolver._get_account_details(
                                    entry.trustee_name, 
                                    entry.trustee_domain
                                )
                                
                                if account_details['type'] in ['Group', 'WellKnownGroup', 'Alias']:
                                    groups_found.add((entry.trustee_name, entry.trustee_domain))
                            else:
                                # Already in cache, assume it's a group
                                groups_found.add((entry.trustee_name, entry.trustee_domain))
                                
                        except Exception:
                            # Skip if we can't determine the type
                            continue
                
                # Convert to list of dictionaries
                result = [
                    {
                        'name': name,
                        'domain': domain,
                        'full_name': f"{domain}\\{name}"
                    }
                    for name, domain in groups_found
                ]
                
                logger.debug(f"Found {len(result)} groups to monitor")
                return result
                
        except Exception as e:
            logger.error(f"Error getting groups to monitor: {str(e)}")
            return []

    async def _check_group_membership_changes(self, group_info: Dict[str, str]) -> List[Dict]:
        """Check for membership changes in a specific group."""
        try:
            group_name = group_info['name']
            domain = group_info['domain']
            full_name = group_info['full_name']
            
            # Get current group membership
            current_membership = await asyncio.get_event_loop().run_in_executor(
                None,
                self.group_resolver.get_group_members,
                group_name,
                domain,
                True  # Include nested groups
            )
            
            # Get previous snapshot
            previous_snapshot = self._membership_snapshots.get(full_name)
            current_time = datetime.utcnow()
            
            # Store current snapshot
            self._membership_snapshots[full_name] = {
                'membership': current_membership,
                'timestamp': current_time,
                'snapshot_time': current_time.isoformat()
            }
            self._last_snapshot_time[full_name] = current_time
            
            if not previous_snapshot:
                logger.debug(f"No previous snapshot for {full_name}, storing initial state")
                return []
            
            # Compare snapshots to detect changes
            changes = await self._compare_group_snapshots(
                full_name, 
                previous_snapshot['membership'], 
                current_membership
            )
            
            return changes
            
        except Exception as e:
            logger.error(f"Error checking group membership for {group_info}: {str(e)}")
            return []

    async def _compare_group_snapshots(self, group_full_name: str, 
                                     previous: Dict, current: Dict) -> List[Dict]:
        """Compare two group membership snapshots to detect changes."""
        try:
            changes = []
            
            # Extract member lists
            prev_all_members = previous.get('all_members', [])
            curr_all_members = current.get('all_members', [])
            
            # Create lookup sets by SID for accurate comparison
            prev_member_sids = {
                member.get('sid'): member 
                for member in prev_all_members 
                if member.get('sid')
            }
            curr_member_sids = {
                member.get('sid'): member 
                for member in curr_all_members 
                if member.get('sid')
            }
            
            # Find added members
            added_sids = set(curr_member_sids.keys()) - set(prev_member_sids.keys())
            for sid in added_sids:
                member = curr_member_sids[sid]
                changes.append({
                    'type': 'member_added',
                    'group': group_full_name,
                    'member_sid': sid,
                    'member_info': member,
                    'change_time': datetime.utcnow(),
                    'access_path': self._trace_member_access_path(member, current)
                })
            
            # Find removed members
            removed_sids = set(prev_member_sids.keys()) - set(curr_member_sids.keys())
            for sid in removed_sids:
                member = prev_member_sids[sid]
                changes.append({
                    'type': 'member_removed',
                    'group': group_full_name,
                    'member_sid': sid,
                    'member_info': member,
                    'change_time': datetime.utcnow(),
                    'access_path': self._trace_member_access_path(member, previous)
                })
            
            # Check for nested group structure changes
            prev_nested = previous.get('nested_groups', [])
            curr_nested = current.get('nested_groups', [])
            
            nested_changes = await self._compare_nested_groups(
                group_full_name, prev_nested, curr_nested
            )
            changes.extend(nested_changes)
            
            return changes
            
        except Exception as e:
            logger.error(f"Error comparing group snapshots: {str(e)}")
            return []

    def _trace_member_access_path(self, member: Dict, group_data: Dict) -> List[str]:
        """Trace how a member gained access through group hierarchy."""
        try:
            access_path = []
            
            # Check if member is directly in the group
            direct_members = group_data.get('direct_members', [])
            if any(m.get('sid') == member.get('sid') for m in direct_members):
                access_path.append('direct')
                return access_path
            
            # Check nested groups
            def find_in_nested(nested_groups, target_sid, current_path):
                for nested_group in nested_groups:
                    group_path = current_path + [nested_group.get('full_name', 'unknown')]
                    
                    # Check direct members of this nested group
                    nested_direct = nested_group.get('direct_members', [])
                    if any(m.get('sid') == target_sid for m in nested_direct):
                        return group_path
                    
                    # Recursively check further nested groups
                    further_nested = nested_group.get('nested_groups', [])
                    if further_nested:
                        result = find_in_nested(further_nested, target_sid, group_path)
                        if result:
                            return result
                
                return None
            
            nested_path = find_in_nested(
                group_data.get('nested_groups', []), 
                member.get('sid'), 
                []
            )
            
            if nested_path:
                access_path.extend(nested_path)
            else:
                access_path.append('unknown')
            
            return access_path
            
        except Exception as e:
            logger.warning(f"Error tracing access path: {str(e)}")
            return ['unknown']

    async def _compare_nested_groups(self, parent_group: str, 
                                   previous: List[Dict], current: List[Dict]) -> List[Dict]:
        """Compare nested group structures for changes."""
        try:
            changes = []
            
            # Create lookup by group name
            prev_nested = {
                group.get('full_name', f"{group.get('domain', '')}\\{group.get('group_name', '')}"): group
                for group in previous
            }
            curr_nested = {
                group.get('full_name', f"{group.get('domain', '')}\\{group.get('group_name', '')}"): group
                for group in current
            }
            
            # Find added nested groups
            added_groups = set(curr_nested.keys()) - set(prev_nested.keys())
            for group_name in added_groups:
                group_info = curr_nested[group_name]
                changes.append({
                    'type': 'nested_group_added',
                    'parent_group': parent_group,
                    'nested_group': group_name,
                    'nested_group_info': group_info,
                    'change_time': datetime.utcnow(),
                    'impact': f"All members of {group_name} now have access through {parent_group}"
                })
            
            # Find removed nested groups
            removed_groups = set(prev_nested.keys()) - set(curr_nested.keys())
            for group_name in removed_groups:
                group_info = prev_nested[group_name]
                changes.append({
                    'type': 'nested_group_removed',
                    'parent_group': parent_group,
                    'nested_group': group_name,
                    'nested_group_info': group_info,
                    'change_time': datetime.utcnow(),
                    'impact': f"Members of {group_name} no longer have access through {parent_group}"
                })
            
            return changes
            
        except Exception as e:
            logger.error(f"Error comparing nested groups: {str(e)}")
            return []

    async def _process_membership_changes(self, changes: List[Dict]) -> None:
        """Process detected membership changes and create database records."""
        try:
            with next(self.db_session_factory()) as db:
                # Create a scan job for these changes
                scan_job = ScanJob(
                    target_id=None,
                    scan_type="group_membership_monitoring",
                    status="completed",
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                    parameters={
                        "changes_count": len(changes),
                        "monitoring_cycle": True,
                        "change_types": list(set(change['type'] for change in changes))
                    }
                )
                db.add(scan_job)
                db.flush()  # Get the scan job ID
                
                # Create permission change records
                for change in changes:
                    try:
                        change_record = PermissionChange(
                            scan_job_id=scan_job.id,
                            change_type=f"group_{change['type']}",
                            previous_state=self._build_change_previous_state(change),
                            current_state=self._build_change_current_state(change),
                            detected_time=change['change_time']
                        )
                        db.add(change_record)
                        
                    except Exception as change_error:
                        logger.warning(f"Error creating change record: {str(change_error)}")
                
                db.commit()
                logger.info(f"Processed {len(changes)} group membership changes")
                
                # Analyze impact of these changes
                await self._analyze_change_impact(changes, scan_job.id)
                
        except Exception as e:
            logger.error(f"Error processing membership changes: {str(e)}", exc_info=True)

    def _build_change_previous_state(self, change: Dict) -> Optional[Dict]:
        """Build previous state data for a change record."""
        try:
            if change['type'] in ['member_removed', 'nested_group_removed']:
                return {
                    'group': change['group'],
                    'member_sid': change.get('member_sid'),
                    'member_info': change.get('member_info'),
                    'nested_group': change.get('nested_group'),
                    'nested_group_info': change.get('nested_group_info'),
                    'access_path': change.get('access_path', [])
                }
            return None
        except Exception as e:
            logger.warning(f"Error building previous state: {str(e)}")
            return None

    def _build_change_current_state(self, change: Dict) -> Dict:
        """Build current state data for a change record."""
        try:
            if change['type'] in ['member_added', 'nested_group_added']:
                return {
                    'group': change['group'],
                    'member_sid': change.get('member_sid'),
                    'member_info': change.get('member_info'),
                    'nested_group': change.get('nested_group'),
                    'nested_group_info': change.get('nested_group_info'),
                    'access_path': change.get('access_path', []),
                    'impact': change.get('impact')
                }
            return {
                'group': change['group'],
                'change_type': change['type'],
                'change_time': change['change_time'].isoformat()
            }
        except Exception as e:
            logger.warning(f"Error building current state: {str(e)}")
            return {'error': str(e)}

    async def _analyze_change_impact(self, changes: List[Dict], scan_job_id: int) -> None:
        """Analyze the impact of group membership changes on file access."""
        try:
            with next(self.db_session_factory()) as db:
                impact_analysis = []
                
                for change in changes:
                    try:
                        # Find what file system paths this group has access to
                        group_name = change['group']
                        
                        # Query recent access entries for this group
                        recent_access = db.query(AccessEntry).join(
                            ScanJob
                        ).filter(
                            and_(
                                AccessEntry.trustee_name == group_name.split('\\')[-1],
                                AccessEntry.trustee_domain == group_name.split('\\')[0],
                                ScanJob.end_time >= datetime.utcnow() - timedelta(days=30),
                                ScanJob.status == "completed"
                            )
                        ).limit(100).all()
                        
                        affected_paths = set()
                        for access in recent_access:
                            if access.scan_result and access.scan_result.path:
                                affected_paths.add(access.scan_result.path)
                        
                        if affected_paths:
                            impact = {
                                'change_id': f"{change['type']}_{change['group']}_{change['change_time'].isoformat()}",
                                'group': change['group'],
                                'change_type': change['type'],
                                'affected_paths': list(affected_paths),
                                'path_count': len(affected_paths),
                                'member_info': change.get('member_info', {}),
                                'access_path': change.get('access_path', [])
                            }
                            
                            impact_analysis.append(impact)
                            
                    except Exception as change_error:
                        logger.warning(f"Error analyzing change impact: {str(change_error)}")
                
                if impact_analysis:
                    logger.info(f"Impact analysis: {len(impact_analysis)} changes "
                               f"affect file system access")
                    
                    # Store impact analysis (could be added to scan job parameters)
                    scan_job = db.query(ScanJob).filter(ScanJob.id == scan_job_id).first()
                    if scan_job:
                        current_params = scan_job.parameters or {}
                        current_params['impact_analysis'] = impact_analysis
                        scan_job.parameters = current_params
                        db.commit()
                
        except Exception as e:
            logger.error(f"Error analyzing change impact: {str(e)}", exc_info=True)

    async def _cleanup_old_snapshots(self) -> None:
        """Clean up old membership snapshots to prevent memory bloat."""
        try:
            current_time = datetime.utcnow()
            cutoff_time = current_time - timedelta(seconds=self.max_snapshot_age)
            
            expired_keys = []
            for key, timestamp in self._last_snapshot_time.items():
                if timestamp < cutoff_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                if key in self._membership_snapshots:
                    del self._membership_snapshots[key]
                if key in self._last_snapshot_time:
                    del self._last_snapshot_time[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired group snapshots")
                
        except Exception as e:
            logger.warning(f"Error cleaning up snapshots: {str(e)}")

    async def force_group_snapshot(self, group_name: str, domain: str) -> Dict:
        """Force a snapshot of a specific group's membership."""
        try:
            logger.info(f"Forcing snapshot for group {domain}\\{group_name}")
            
            membership = await asyncio.get_event_loop().run_in_executor(
                None,
                self.group_resolver.get_group_members,
                group_name,
                domain,
                True
            )
            
            full_name = f"{domain}\\{group_name}"
            current_time = datetime.utcnow()
            
            self._membership_snapshots[full_name] = {
                'membership': membership,
                'timestamp': current_time,
                'snapshot_time': current_time.isoformat()
            }
            self._last_snapshot_time[full_name] = current_time
            
            return {
                'group': full_name,
                'snapshot_time': current_time.isoformat(),
                'total_members': membership.get('total_all_members', 0),
                'direct_members': membership.get('total_direct_members', 0),
                'nested_groups': len(membership.get('nested_groups', []))
            }
            
        except Exception as e:
            logger.error(f"Error forcing group snapshot: {str(e)}")
            raise

    async def get_group_membership_history(self, group_name: str, domain: str, 
                                         days: int = 7) -> List[Dict]:
        """Get membership change history for a specific group."""
        try:
            full_name = f"{domain}\\{group_name}"
            
            with next(self.db_session_factory()) as db:
                # Get permission changes related to this group
                cutoff_time = datetime.utcnow() - timedelta(days=days)
                
                changes = db.query(PermissionChange).filter(
                    and_(
                        PermissionChange.detected_time >= cutoff_time,
                        PermissionChange.change_type.like('group_%')
                    )
                ).order_by(desc(PermissionChange.detected_time)).all()
                
                # Filter changes related to this specific group
                group_changes = []
                for change in changes:
                    try:
                        current_state = change.current_state or {}
                        previous_state = change.previous_state or {}
                        
                        if (current_state.get('group') == full_name or 
                            previous_state.get('group') == full_name):
                            
                            group_changes.append({
                                'id': change.id,
                                'change_type': change.change_type,
                                'detected_time': change.detected_time.isoformat(),
                                'previous_state': change.previous_state,
                                'current_state': change.current_state,
                                'scan_job_id': change.scan_job_id
                            })
                            
                    except Exception as change_error:
                        logger.warning(f"Error processing change record: {str(change_error)}")
                
                return group_changes
                
        except Exception as e:
            logger.error(f"Error getting group membership history: {str(e)}")
            return []

    async def get_monitoring_status(self) -> Dict:
        """Get current monitoring status and statistics."""
        try:
            return {
                'monitoring_active': self._monitoring,
                'groups_monitored': len(self._membership_snapshots),
                'last_snapshot_times': {
                    group: timestamp.isoformat()
                    for group, timestamp in self._last_snapshot_time.items()
                },
                'configuration': {
                    'snapshot_interval': self.snapshot_interval,
                    'change_detection_interval': self.change_detection_interval,
                    'max_snapshot_age': self.max_snapshot_age
                },
                'cache_stats': {
                    'snapshots_cached': len(self._membership_snapshots),
                    'memory_usage_estimate': len(str(self._membership_snapshots))
                }
            }
        except Exception as e:
            logger.error(f"Error getting monitoring status: {str(e)}")
            return {'error': str(e)}