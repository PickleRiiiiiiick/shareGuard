# src/scanner/file_scanner.py
import os
import win32security
import win32api
import win32con
import ntsecuritycon
from datetime import datetime
from typing import Dict, List, Optional, Set
from pathlib import Path
import logging
from ..utils.logger import setup_logger
from .group_resolver import GroupResolver

logger = setup_logger('scanner')

class PermissionScanner:
    """Core scanner class for analyzing Windows file system permissions."""
    
    def __init__(self):
        # Define permission categories
        self.permission_categories = {
            'Basic': {
                ntsecuritycon.GENERIC_READ: "Read",
                ntsecuritycon.GENERIC_WRITE: "Write",
                ntsecuritycon.GENERIC_EXECUTE: "Execute",
                ntsecuritycon.GENERIC_ALL: "Full Control"
            },
            'Advanced': {
                ntsecuritycon.DELETE: "Delete",
                ntsecuritycon.READ_CONTROL: "Read Permissions",
                ntsecuritycon.WRITE_DAC: "Change Permissions",
                ntsecuritycon.WRITE_OWNER: "Take Ownership"
            },
            'Directory': {
                ntsecuritycon.FILE_LIST_DIRECTORY: "List Folder",
                ntsecuritycon.FILE_ADD_FILE: "Create Files",
                ntsecuritycon.FILE_ADD_SUBDIRECTORY: "Create Folders",
                ntsecuritycon.FILE_READ_EA: "Read Extended Attributes",
                ntsecuritycon.FILE_WRITE_EA: "Write Extended Attributes",
                ntsecuritycon.FILE_TRAVERSE: "Traverse Folder",
                ntsecuritycon.FILE_DELETE_CHILD: "Delete Subfolders and Files",
                ntsecuritycon.FILE_READ_ATTRIBUTES: "Read Attributes",
                ntsecuritycon.FILE_WRITE_ATTRIBUTES: "Write Attributes"
            }
        }
        
        # System accounts configuration
        self.system_accounts = {
            'NT AUTHORITY\\SYSTEM',
            'NT AUTHORITY\\Authenticated Users',
            'BUILTIN\\Administrators',
            'BUILTIN\\Users',
            'BUILTIN\\Power Users',
            'NT SERVICE\\',
            'CREATOR OWNER'
        }
        
        self.group_resolver = GroupResolver()
        logger.info("PermissionScanner initialized with categorized Windows permissions")

    def _is_system_account(self, account_name: str) -> bool:
        """Check if the account is a system account."""
        return (account_name in self.system_accounts or 
                any(account_name.startswith(prefix) for prefix in ['NT ', 'BUILTIN\\', 'NT SERVICE\\']))

    def _get_trustee_name(self, sid: bytes) -> Dict[str, str]:
        """Convert a security identifier (SID) to a readable name."""
        try:
            name, domain, _ = win32security.LookupAccountSid(None, sid)
            trustee_info = {
                "name": name,
                "domain": domain,
                "sid": win32security.ConvertSidToStringSid(sid),
                "full_name": f"{domain}\\{name}"
            }
            trustee_info["is_system"] = self._is_system_account(trustee_info["full_name"])
            return trustee_info
        except Exception as e:
            logger.warning(f"Could not resolve SID: {str(e)}")
            sid_string = win32security.ConvertSidToStringSid(sid)
            return {
                "name": "Unknown",
                "domain": "Unknown",
                "sid": sid_string,
                "full_name": f"Unknown SID: {sid_string}",
                "is_system": False
            }

    def _get_categorized_permissions(self, access_mask: int, simplified: bool = False) -> Dict[str, List[str]]:
        """Convert access mask to categorized list of permission names."""
        if simplified:
            return {"type": "Full Access" if access_mask & ntsecuritycon.GENERIC_ALL else "Limited Access"}
            
        permissions = {category: [] for category in self.permission_categories.keys()}
        
        # Check for full control first
        if access_mask & ntsecuritycon.GENERIC_ALL == ntsecuritycon.GENERIC_ALL:
            permissions['Basic'] = ["Full Control"]
            return permissions
            
        # Check each category
        for category, flags in self.permission_categories.items():
            for flag, permission_name in flags.items():
                if access_mask & flag == flag:
                    permissions[category].append(permission_name)
        
        return {k: sorted(v) for k, v in permissions.items() if v}

    def get_folder_permissions(
        self, 
        folder_path: str, 
        simplified_system: bool = True,
        include_inherited: bool = True
    ) -> Dict:
        """
        Get detailed permission information for a specific folder.
        
        Args:
            folder_path: Path to scan
            simplified_system: If True, provides simplified information for system accounts
            include_inherited: Include inherited permissions
        """
        logger.info(f"Analyzing permissions for: {folder_path}")
        
        try:
            if not os.path.exists(folder_path):
                raise FileNotFoundError(f"Path does not exist: {folder_path}")

            # Get security descriptor
            sd = win32security.GetFileSecurity(
                folder_path,
                win32security.DACL_SECURITY_INFORMATION | 
                win32security.OWNER_SECURITY_INFORMATION |
                win32security.GROUP_SECURITY_INFORMATION
            )

            # Get owner information
            owner_sid = sd.GetSecurityDescriptorOwner()
            owner_info = self._get_trustee_name(owner_sid)

            # Get primary group information
            group_sid = sd.GetSecurityDescriptorGroup()
            group_info = self._get_trustee_name(group_sid)

            # Get DACL
            dacl = sd.GetSecurityDescriptorDacl()
            
            # Process ACEs
            aces = []
            if dacl:
                for ace_index in range(dacl.GetAceCount()):
                    ace = dacl.GetAce(ace_index)
                    is_inherited = bool(ace[0][1] & win32security.INHERITED_ACE)
                    
                    # Skip inherited permissions if not requested
                    if is_inherited and not include_inherited:
                        continue
                        
                    trustee_info = self._get_trustee_name(ace[2])
                    is_system = trustee_info.get("is_system", False)
                    
                    # Create basic ACE info
                    ace_info = {
                        "trustee": trustee_info,
                        "type": "Allow" if ace[0][0] == win32security.ACCESS_ALLOWED_ACE_TYPE else "Deny",
                        "inherited": is_inherited,
                        "is_system": is_system
                    }
                    
                    # Add permissions based on account type
                    if is_system and simplified_system:
                        ace_info["permissions"] = self._get_categorized_permissions(ace[1], simplified=True)
                    else:
                        ace_info["permissions"] = self._get_categorized_permissions(ace[1])
                        ace_info["access_paths"] = self.group_resolver.get_access_paths(trustee_info)

                    aces.append(ace_info)

            scan_time = datetime.now().isoformat()
            
            # Build folder info
            folder = Path(folder_path)
            folder_info = {
                "name": folder.name,
                "path": str(folder),
                "parent": str(folder.parent),
                "is_root": folder.parent == folder
            }

            return {
                "path": folder_path,
                "folder_info": folder_info,
                "owner": owner_info,
                "primary_group": group_info,
                "aces": aces,
                "scan_time": scan_time,
                "success": True,
                "metadata": {
                    "has_system_accounts": any(ace["is_system"] for ace in aces),
                    "total_aces": len(aces),
                    "system_aces": sum(1 for ace in aces if ace["is_system"]),
                    "non_system_aces": sum(1 for ace in aces if not ace["is_system"]),
                }
            }

        except Exception as e:
            logger.error(f"Error scanning {folder_path}: {str(e)}", exc_info=True)
            return {
                "path": folder_path,
                "error": str(e),
                "scan_time": datetime.now().isoformat(),
                "success": False
            }

    def scan_directory(
        self,
        root_path: str,
        recursive: bool = True,
        max_depth: Optional[int] = None,
        simplified_system: bool = True
    ) -> Dict:
        """
        Scan a directory and optionally its subdirectories for permissions.
        
        Args:
            root_path: Root directory to scan
            recursive: Whether to scan subdirectories
            max_depth: Maximum depth for recursive scanning
            simplified_system: Whether to use simplified system account information
        """
        logger.info(f"Starting directory scan at: {root_path}")
        
        def _scan_recursive(path: str, current_depth: int) -> Dict:
            try:
                # Scan current directory
                results = self.get_folder_permissions(path, simplified_system)
                results["subfolders"] = []
                results["statistics"] = {
                    "total_folders": 1,
                    "processed_folders": 1,
                    "error_count": 0,
                    "system_aces_count": results["metadata"]["system_aces"],
                    "non_system_aces_count": results["metadata"]["non_system_aces"]
                }
                
                # Process subdirectories if needed
                if recursive and (max_depth is None or current_depth < max_depth):
                    try:
                        for item in os.scandir(path):
                            if item.is_dir():
                                subfolder_results = _scan_recursive(item.path, current_depth + 1)
                                if subfolder_results["success"]:
                                    results["subfolders"].append(subfolder_results)
                                    # Update statistics
                                    results["statistics"]["total_folders"] += subfolder_results["statistics"]["total_folders"]
                                    results["statistics"]["processed_folders"] += subfolder_results["statistics"]["processed_folders"]
                                    results["statistics"]["error_count"] += subfolder_results["statistics"]["error_count"]
                                    results["statistics"]["system_aces_count"] += subfolder_results["statistics"]["system_aces_count"]
                                    results["statistics"]["non_system_aces_count"] += subfolder_results["statistics"]["non_system_aces_count"]
                                else:
                                    results["statistics"]["error_count"] += 1
                    except PermissionError:
                        results["access_error"] = "Permission denied for some subfolders"
                        results["statistics"]["error_count"] += 1
                
                return results
                
            except Exception as e:
                logger.error(f"Error in recursive scan: {str(e)}", exc_info=True)
                return {
                    "path": path,
                    "error": str(e),
                    "scan_time": datetime.now().isoformat(),
                    "success": False,
                    "statistics": {
                        "total_folders": 1,
                        "processed_folders": 0,
                        "error_count": 1,
                        "system_aces_count": 0,
                        "non_system_aces_count": 0
                    }
                }

        return _scan_recursive(root_path, 0)