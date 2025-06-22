# src/core/scanner.py
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import logging
from src.scanner.file_scanner import PermissionScanner
from src.scanner.group_resolver import GroupResolver
from src.utils.logger import setup_logger
from config.settings import SCANNER_CONFIG

logger = setup_logger('core_scanner')

class ShareGuardScanner:
    """Core ShareGuard scanning functionality."""
    
    def __init__(self):
        self.permission_scanner = PermissionScanner()
        self.group_resolver = GroupResolver()
        self.max_depth = SCANNER_CONFIG['max_depth']
        self.batch_size = SCANNER_CONFIG['batch_size']
        self.excluded_paths = set(SCANNER_CONFIG['excluded_paths'])
        logger.info("ShareGuard Core Scanner initialized")

    def _should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded from scanning."""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)

    def scan_path(
        self, 
        path: str, 
        include_subfolders: bool = False, 
        max_depth: Optional[int] = None,
        simplified_system: bool = True,
        include_inherited: bool = True
    ) -> Dict:
        """
        Scan a specific path for permissions.
        
        Args:
            path: Path to scan
            include_subfolders: Whether to include subfolders
            max_depth: Maximum depth for subfolder scanning (overrides config)
            simplified_system: Whether to use simplified system account information
            include_inherited: Whether to include inherited permissions
        """
        try:
            # Input validation
            folder_path = Path(path)
            if not folder_path.exists():
                return {
                    "success": False,
                    "error": "Path does not exist",
                    "path": path,
                    "scan_time": datetime.now().isoformat()
                }

            if self._should_exclude_path(str(folder_path)):
                return {
                    "success": False,
                    "error": "Path is in exclusion list",
                    "path": path,
                    "scan_time": datetime.now().isoformat()
                }

            # Get base folder permissions
            base_results = self.permission_scanner.get_folder_permissions(
                str(folder_path),
                simplified_system=simplified_system,
                include_inherited=include_inherited
            )
            
            # Add metadata
            results = {
                "success": True,
                "scan_time": datetime.now().isoformat(),
                "folder_info": {
                    "name": folder_path.name,
                    "path": str(folder_path),
                    "parent": str(folder_path.parent),
                    "is_root": folder_path.parent == folder_path
                },
                "permissions": base_results,
                "subfolders": [],
                "statistics": {
                    "total_folders": 1,
                    "processed_folders": 1,
                    "error_count": 0,
                    "system_accounts": base_results.get("metadata", {}).get("system_aces", 0),
                    "non_system_accounts": base_results.get("metadata", {}).get("non_system_aces", 0)
                }
            }

            # Add subfolder scanning if requested
            if include_subfolders:
                depth_limit = max_depth if max_depth is not None else self.max_depth
                if depth_limit > 0:
                    try:
                        for subfolder in folder_path.iterdir():
                            if subfolder.is_dir() and not self._should_exclude_path(str(subfolder)):
                                subfolder_results = self.scan_path(
                                    str(subfolder),
                                    include_subfolders=True,
                                    max_depth=depth_limit - 1,
                                    simplified_system=simplified_system,
                                    include_inherited=include_inherited
                                )
                                results["subfolders"].append(subfolder_results)
                                
                                # Update statistics
                                if subfolder_results["success"]:
                                    stats = results["statistics"]
                                    subfolder_stats = subfolder_results["statistics"]
                                    stats["total_folders"] += subfolder_stats["total_folders"]
                                    stats["processed_folders"] += subfolder_stats["processed_folders"]
                                    stats["error_count"] += subfolder_stats["error_count"]
                                    stats["system_accounts"] += subfolder_stats.get("system_accounts", 0)
                                    stats["non_system_accounts"] += subfolder_stats.get("non_system_accounts", 0)
                                else:
                                    results["statistics"]["error_count"] += 1
                    except PermissionError:
                        results["access_error"] = "Permission denied for some subfolders"
                        results["statistics"]["error_count"] += 1

            return results

        except Exception as e:
            logger.error(f"Error scanning path {path}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "path": path,
                "scan_time": datetime.now().isoformat(),
                "statistics": {
                    "total_folders": 1,
                    "processed_folders": 0,
                    "error_count": 1,
                    "system_accounts": 0,
                    "non_system_accounts": 0
                }
            }

    def get_user_access(self, username: str, domain: str, base_path: Optional[str] = None) -> Dict:
        """Get all accessible folders for a user."""
        try:
            # Get user's groups
            user_info = {
                "name": username,
                "domain": domain,
                "full_name": f"{domain}\\{username}"
            }
            
            logger.info(f"Analyzing access for user: {user_info['full_name']}")
            
            groups = self.group_resolver._get_user_groups(username, domain)
            access_paths = self.group_resolver.get_access_paths(user_info)
            
            results = {
                "success": True,
                "scan_time": datetime.now().isoformat(),
                "user_info": user_info,
                "group_memberships": groups,
                "access_paths": access_paths,
                "accessible_folders": [],
                "statistics": {
                    "total_groups": len(groups),
                    "folders_checked": 0,
                    "accessible_folders": 0,
                    "error_count": 0
                }
            }

            # If base path provided, scan for accessible folders
            if base_path:
                base_folder = Path(base_path)
                if not base_folder.exists():
                    raise FileNotFoundError(f"Base path does not exist: {base_path}")

                # Get all folders to check
                folders_to_check = [base_folder]
                if self.max_depth > 0:
                    try:
                        folders_to_check.extend(
                            f for f in base_folder.rglob("*") 
                            if f.is_dir() and not self._should_exclude_path(str(f))
                        )
                    except PermissionError:
                        results["access_error"] = "Permission denied for some subfolders"
                        results["statistics"]["error_count"] += 1

                # Check each folder
                for folder in folders_to_check:
                    results["statistics"]["folders_checked"] += 1
                    
                    try:
                        folder_perms = self.permission_scanner.get_folder_permissions(str(folder))
                        if folder_perms["success"]:
                            # Check if user has access through any group
                            has_access = False
                            effective_permissions = {
                                'Basic': set(),
                                'Advanced': set(),
                                'Directory': set()
                            }
                            matching_aces = []
                            
                            for ace in folder_perms.get("aces", []):
                                trustee = ace["trustee"]
                                # Check direct user match or group membership
                                if (trustee["full_name"] == user_info["full_name"] or
                                    any(group["full_name"] == trustee["full_name"] for group in groups)):
                                    has_access = True
                                    # Accumulate permissions
                                    for category, perms in ace["permissions"].items():
                                        effective_permissions[category].update(perms)
                                    
                                    # Include ACE details for reporting
                                    ace_copy = ace.copy()
                                    ace_copy['inherited'] = ace.get('inherited', False)
                                    matching_aces.append(ace_copy)
                            
                            if has_access:
                                results["statistics"]["accessible_folders"] += 1
                                results["accessible_folders"].append({
                                    "path": str(folder),
                                    "effective_permissions": {
                                        k: sorted(v) for k, v in effective_permissions.items() if v
                                    },
                                    "aces": matching_aces
                                })
                    
                    except Exception as e:
                        logger.error(f"Error checking folder {folder}: {str(e)}")
                        results["statistics"]["error_count"] += 1

            return results

        except Exception as e:
            logger.error(f"Error analyzing user access: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "scan_time": datetime.now().isoformat(),
                "user_info": user_info if 'user_info' in locals() else None
            }

    def get_folder_structure(
        self, 
        root_path: str, 
        max_depth: Optional[int] = None,
        simplified_system: bool = True
    ) -> Dict:
        """
        Get folder structure with permission information.
        
        Args:
            root_path: Starting path for structure analysis
            max_depth: Maximum folder depth to traverse
            simplified_system: Whether to use simplified system account information
        """
        try:
            folder_path = Path(root_path)
            if not folder_path.exists():
                return {
                    "success": False,
                    "error": "Path does not exist",
                    "path": root_path,
                    "scan_time": datetime.now().isoformat()
                }

            if self._should_exclude_path(str(folder_path)):
                return {
                    "success": False,
                    "error": "Path is in exclusion list",
                    "path": root_path,
                    "scan_time": datetime.now().isoformat()
                }

            depth_limit = max_depth if max_depth is not None else self.max_depth
            
            structure = {
                "success": True,
                "scan_time": datetime.now().isoformat(),
                "name": folder_path.name,
                "path": str(folder_path),
                "type": "directory",
                "permissions": self.permission_scanner.get_folder_permissions(
                    str(folder_path),
                    simplified_system=simplified_system
                ),
                "children": [],
                "statistics": {
                    "total_folders": 1,
                    "processed_folders": 1,
                    "error_count": 0,
                    "system_accounts": 0,
                    "non_system_accounts": 0
                }
            }

            if depth_limit > 0:
                try:
                    for item in folder_path.iterdir():
                        if item.is_dir() and not self._should_exclude_path(str(item)):
                            child_structure = self.get_folder_structure(
                                str(item),
                                max_depth=depth_limit - 1,
                                simplified_system=simplified_system
                            )
                            structure["children"].append(child_structure)
                            
                            # Update statistics
                            if child_structure["success"]:
                                stats = structure["statistics"]
                                child_stats = child_structure["statistics"]
                                stats["total_folders"] += child_stats["total_folders"]
                                stats["processed_folders"] += child_stats["processed_folders"]
                                stats["error_count"] += child_stats["error_count"]
                                stats["system_accounts"] += child_stats["system_accounts"]
                                stats["non_system_accounts"] += child_stats["non_system_accounts"]
                            else:
                                structure["statistics"]["error_count"] += 1
                                
                except PermissionError:
                    structure["access_error"] = "Permission denied"
                    structure["statistics"]["error_count"] += 1

            return structure

        except Exception as e:
            logger.error(f"Error getting folder structure: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "path": root_path,
                "scan_time": datetime.now().isoformat(),
                "statistics": {
                    "total_folders": 1,
                    "processed_folders": 0,
                    "error_count": 1,
                    "system_accounts": 0,
                    "non_system_accounts": 0
                }
            }

# Create global scanner instance
scanner = ShareGuardScanner()