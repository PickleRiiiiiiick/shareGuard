# src/services/change_monitor.py

import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from pathlib import Path
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.db.database import get_db_sync
from src.db.models.changes import PermissionChange
from src.db.models.alerts import Alert, AlertConfiguration
from src.db.models.folder_cache import FolderPermissionCache
from src.services.cache_service import cache_service
from src.services.notification_service import notification_service
from src.core.scanner import scanner
from src.utils.logger import setup_logger

logger = setup_logger('change_monitor')

class ChangeMonitorService:
    """Service for monitoring permission changes and updating cache."""
    
    def __init__(self):
        self.monitoring_paths: Set[str] = set()
        self.is_monitoring = False
        self.check_interval = 60  # 1 minute for testing (was 5 minutes)
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def start_monitoring(self, paths: Optional[List[str]] = None) -> None:
        """Start monitoring for permission changes."""
        try:
            if paths:
                self.monitoring_paths.update(paths)
            
            if self.is_monitoring:
                logger.info("Monitoring already active")
                return
            
            self.is_monitoring = True
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info(f"Started monitoring {len(self.monitoring_paths)} paths")
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {str(e)}")
            self.is_monitoring = False
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring for changes."""
        try:
            self.is_monitoring = False
            
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
                self._monitor_task = None
            
            logger.info("Stopped monitoring")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {str(e)}")
    
    async def add_monitoring_path(self, path: str) -> None:
        """Add a path to monitor."""
        normalized_path = str(Path(path).resolve())
        self.monitoring_paths.add(normalized_path)
        logger.info(f"Added monitoring path: {normalized_path}")
    
    async def remove_monitoring_path(self, path: str) -> None:
        """Remove a path from monitoring."""
        normalized_path = str(Path(path).resolve())
        self.monitoring_paths.discard(normalized_path)
        logger.info(f"Removed monitoring path: {normalized_path}")
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                await self._check_for_changes()
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {str(e)}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def _check_for_changes(self) -> None:
        """Check all monitored paths for changes."""
        try:
            db = next(get_db_sync())
            
            for path in list(self.monitoring_paths):
                if not os.path.exists(path):
                    logger.warning(f"Monitored path no longer exists: {path}")
                    self.monitoring_paths.discard(path)
                    continue
                
                await self._check_path_changes(db, path)
            
            # Cleanup old stale cache entries
            cache_service.cleanup_stale_cache(db, older_than_hours=48)
            
        except Exception as e:
            logger.error(f"Error checking for changes: {str(e)}")
        finally:
            db.close()
    
    async def _check_path_changes(self, db: Session, path: str) -> None:
        """Check a specific path for permission changes."""
        try:
            # Get cached permissions
            cache_entry = db.query(FolderPermissionCache).filter(
                FolderPermissionCache.folder_path == path
            ).first()
            
            if not cache_entry:
                # No cache entry, create one
                logger.info(f"Creating initial cache entry for: {path}")
                permissions = scanner.permission_scanner.get_folder_permissions(
                    path, simplified_system=True
                )
                cache_service._update_permission_cache(db, path, permissions)
                return
            
            # Get current permissions
            current_permissions = scanner.permission_scanner.get_folder_permissions(
                path, simplified_system=True
            )
            
            # Calculate checksum
            current_checksum = hashlib.sha256(
                json.dumps(current_permissions, sort_keys=True).encode()
            ).hexdigest()
            
            # Compare with cached checksum
            if cache_entry.checksum != current_checksum:
                logger.info(f"Detected potential permission change for: {path}")
                
                # Check if there are significant changes before proceeding
                has_significant_changes = await self._record_permission_change(
                    db, 
                    path, 
                    cache_entry.permissions_data, 
                    current_permissions
                )
                
                if has_significant_changes:
                    logger.info(f"Confirmed significant permission change for: {path}")
                    
                    # Update cache only after confirming significant changes
                    cache_service._update_permission_cache(db, path, current_permissions)
                    
                    # Mark dependent caches as stale
                    cache_service.mark_path_stale(db, path)
                    
                    # Send notification
                    await self._send_change_notification(path, cache_entry.permissions_data, current_permissions)
                else:
                    logger.debug(f"No significant changes detected for: {path}, skipping alert")
                
        except Exception as e:
            logger.error(f"Error checking path {path}: {str(e)}")
    
    async def _record_permission_change(
        self, 
        db: Session, 
        path: str, 
        old_permissions: Dict, 
        new_permissions: Dict
    ) -> bool:
        """Record a permission change in the database. Returns True if significant changes were found."""
        try:
            # Analyze changes
            changes = self._analyze_permission_changes(old_permissions, new_permissions)
            
            # Check if there are any significant changes
            significant_changes = any([
                changes["permissions_added"],
                changes["permissions_removed"], 
                changes["permissions_modified"],
                changes["owner_changed"],
                changes["inheritance_changed"]
            ])
            
            if not significant_changes:
                return False  # No significant changes, don't record
            
            for change_type, details in changes.items():
                if details:
                    change = PermissionChange(
                        change_type=change_type,
                        detected_time=datetime.utcnow(),
                        previous_state=old_permissions,
                        current_state=new_permissions
                    )
                    db.add(change)
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error recording permission change: {str(e)}")
            db.rollback()
            return False
    
    def _analyze_permission_changes(self, old_perms: Dict, new_perms: Dict) -> Dict:
        """Analyze differences between old and new permissions."""
        changes = {
            "permissions_added": [],
            "permissions_removed": [],
            "permissions_modified": [],
            "owner_changed": None,
            "inheritance_changed": None
        }
        
        # Check owner change
        old_owner = old_perms.get("owner", {})
        new_owner = new_perms.get("owner", {})
        if old_owner.get("full_name") != new_owner.get("full_name"):
            changes["owner_changed"] = {
                "old": old_owner.get("full_name"),
                "new": new_owner.get("full_name")
            }
        
        # Check inheritance change
        old_inheritance = old_perms.get("inheritance_enabled")
        new_inheritance = new_perms.get("inheritance_enabled")
        if old_inheritance != new_inheritance:
            changes["inheritance_changed"] = {
                "old": old_inheritance,
                "new": new_inheritance
            }
        
        # Check ACE changes
        old_aces = {self._ace_key(ace): ace for ace in old_perms.get("aces", [])}
        new_aces = {self._ace_key(ace): ace for ace in new_perms.get("aces", [])}
        
        # Find removed ACEs
        for key, ace in old_aces.items():
            if key not in new_aces:
                changes["permissions_removed"].append({
                    "trustee": ace.get("trustee", {}).get("full_name"),
                    "permissions": ace.get("permissions", {})
                })
        
        # Find added ACEs
        for key, ace in new_aces.items():
            if key not in old_aces:
                changes["permissions_added"].append({
                    "trustee": ace.get("trustee", {}).get("full_name"),
                    "permissions": ace.get("permissions", {})
                })
            elif old_aces[key].get("permissions") != ace.get("permissions"):
                # Modified permissions
                changes["permissions_modified"].append({
                    "trustee": ace.get("trustee", {}).get("full_name"),
                    "old_permissions": old_aces[key].get("permissions", {}),
                    "new_permissions": ace.get("permissions", {})
                })
        
        return changes
    
    def _ace_key(self, ace: Dict) -> str:
        """Generate a unique key for an ACE."""
        trustee = ace.get("trustee", {})
        # Use the correct field names from the actual ACE structure
        return f"{trustee.get('sid', '')}_{ace.get('type', '')}_{ace.get('inherited', False)}"
    
    async def _send_change_notification(
        self, 
        path: str, 
        old_permissions: Dict, 
        new_permissions: Dict
    ) -> None:
        """Send notification about permission change."""
        try:
            changes = self._analyze_permission_changes(old_permissions, new_permissions)
            
            # Create alert in database
            db = next(get_db_sync())
            try:
                alert = Alert(
                    severity="high" if any(changes.values()) else "medium",
                    message=self._format_change_message(path, changes),
                    details=self._format_alert_details(path, changes)
                )
                db.add(alert)
                db.commit()
                
                # Send WebSocket notification
                change_record = PermissionChange(
                    change_type="permission_change",
                    detected_time=datetime.utcnow(),
                    previous_state=old_permissions,
                    current_state=new_permissions
                )
                
                await notification_service.send_permission_change_notification(change_record)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error sending change notification: {str(e)}")
    
    def _format_change_message(self, path: str, changes: Dict) -> str:
        """Format a human-readable change message."""
        parts = []
        
        # Format folder name for better readability
        folder_name = path.split("\\")[-1] if "\\" in path else path
        
        if changes["owner_changed"]:
            old_owner = changes['owner_changed']['old'] or "Unknown"
            new_owner = changes['owner_changed']['new'] or "Unknown"
            parts.append(f"🔄 Owner changed: {old_owner} → {new_owner}")
        
        if changes["inheritance_changed"]:
            status = "enabled" if changes['inheritance_changed']['new'] else "disabled"
            parts.append(f"🔗 Inheritance {status}")
        
        if changes["permissions_added"]:
            count = len(changes['permissions_added'])
            parts.append(f"➕ {count} permission{'s' if count != 1 else ''} added")
        
        if changes["permissions_removed"]:
            count = len(changes['permissions_removed'])
            parts.append(f"➖ {count} permission{'s' if count != 1 else ''} removed")
        
        if changes["permissions_modified"]:
            count = len(changes['permissions_modified'])
            parts.append(f"🔧 {count} permission{'s' if count != 1 else ''} modified")
        
        if not parts:
            return f"📁 Permission structure changed for {folder_name}"
        
        return f"📁 {folder_name}: " + ", ".join(parts)
    
    def _format_alert_details(self, path: str, changes: Dict) -> Dict:
        """Format alert details in a user-friendly way."""
        folder_name = path.split("\\")[-1] if "\\" in path else path
        
        details = {
            "folder": {
                "name": folder_name,
                "full_path": path
            },
            "summary": {
                "changes_detected": 0,
                "severity_level": "medium"
            },
            "changes": [],
            "metadata": {
                "detected_at": datetime.utcnow().isoformat(),
                "source": "Real-time Monitoring",
                "alert_type": "Permission Change"
            }
        }
        
        # Owner changes
        if changes["owner_changed"]:
            details["changes"].append({
                "type": "Owner Change",
                "icon": "🔄",
                "description": f"Folder owner changed from '{changes['owner_changed']['old'] or 'Unknown'}' to '{changes['owner_changed']['new'] or 'Unknown'}'",
                "impact": "High - Ownership changes can affect access control"
            })
            details["summary"]["severity_level"] = "high"
            
        # Inheritance changes
        if changes["inheritance_changed"]:
            status = "enabled" if changes['inheritance_changed']['new'] else "disabled"
            details["changes"].append({
                "type": "Inheritance Setting",
                "icon": "🔗",
                "description": f"Permission inheritance {status}",
                "impact": "Medium - Affects how permissions are inherited from parent folders"
            })
            
        # Permission additions
        if changes["permissions_added"]:
            count = len(changes['permissions_added'])
            user_list = [perm.get('trustee', 'Unknown User') for perm in changes['permissions_added'][:3]]
            details["changes"].append({
                "type": "Permissions Added",
                "icon": "➕",
                "description": f"{count} new permission{'s' if count != 1 else ''} granted",
                "users_affected": user_list,
                "impact": "Medium - New users/groups can access this folder"
            })
            
        # Permission removals
        if changes["permissions_removed"]:
            count = len(changes['permissions_removed'])
            user_list = [perm.get('trustee', 'Unknown User') for perm in changes['permissions_removed'][:3]]
            details["changes"].append({
                "type": "Permissions Removed",
                "icon": "➖",
                "description": f"{count} permission{'s' if count != 1 else ''} revoked",
                "users_affected": user_list,
                "impact": "High - Users/groups lost access to this folder"
            })
            details["summary"]["severity_level"] = "high"
            
        # Permission modifications
        if changes["permissions_modified"]:
            count = len(changes['permissions_modified'])
            user_list = [perm.get('trustee', 'Unknown User') for perm in changes['permissions_modified'][:3]]
            details["changes"].append({
                "type": "Permissions Modified",
                "icon": "🔧",
                "description": f"{count} permission{'s' if count != 1 else ''} changed",
                "users_affected": user_list,
                "impact": "Medium - Access levels changed for existing users/groups"
            })
        
        details["summary"]["changes_detected"] = len(details["changes"])
        
        return details

# Global change monitor instance
change_monitor = ChangeMonitorService()