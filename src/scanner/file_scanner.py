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
        self.group_resolver = GroupResolver()
        logger.info("PermissionScanner initialized with categorized Windows permissions")

    def _get_trustee_name(self, sid: bytes) -> Dict[str, str]:
        """Convert a security identifier (SID) to a readable name."""
        try:
            name, domain, _ = win32security.LookupAccountSid(None, sid)
            return {
                "name": name,
                "domain": domain,
                "sid": win32security.ConvertSidToStringSid(sid),
                "full_name": f"{domain}\\{name}"
            }
        except Exception as e:
            logger.warning(f"Could not resolve SID: {str(e)}")
            sid_string = win32security.ConvertSidToStringSid(sid)
            return {
                "name": "Unknown",
                "domain": "Unknown",
                "sid": sid_string,
                "full_name": f"Unknown SID: {sid_string}"
            }

    def _get_categorized_permissions(self, access_mask: int) -> Dict[str, List[str]]:
        """Convert access mask to categorized list of permission names."""
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

    def _consolidate_aces(self, aces: List[Dict]) -> List[Dict]:
        """Consolidate multiple ACEs for the same trustee, preserving access paths."""
        consolidated = {}
        
        for ace in aces:
            trustee_key = ace['trustee']['full_name']
            if trustee_key not in consolidated:
                consolidated[trustee_key] = {
                    'trustee': ace['trustee'],
                    'type': ace['type'],
                    'inherited': ace['inherited'],
                    'permissions': {'Basic': set(), 'Advanced': set(), 'Directory': set()},
                    'access_paths': ace['access_paths']
                }
            
            # Merge permissions by category
            for category, perms in ace['permissions'].items():
                consolidated[trustee_key]['permissions'][category].update(perms)
        
        # Convert sets back to sorted lists
        result = []
        for entry in consolidated.values():
            entry['permissions'] = {k: sorted(v) for k, v in entry['permissions'].items() if v}
            result.append(entry)
            
        return result

    def get_folder_permissions(self, folder_path: str) -> Dict:
        """Get detailed permission information for a specific folder."""
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
                    trustee_info = self._get_trustee_name(ace[2])
                    
                    # Get access paths for this trustee
                    access_paths = self.group_resolver.get_access_paths(trustee_info)
                    
                    ace_type = "Allow" if ace[0][0] == win32security.ACCESS_ALLOWED_ACE_TYPE else "Deny"
                    
                    ace_info = {
                        "trustee": trustee_info,
                        "type": ace_type,
                        "inherited": bool(ace[0][0] & win32security.INHERITED_ACE),
                        "permissions": self._get_categorized_permissions(ace[1]),
                        "access_paths": access_paths
                    }
                    aces.append(ace_info)

            # Consolidate ACEs
            consolidated_aces = self._consolidate_aces(aces)

            return {
                "path": folder_path,
                "owner": owner_info,
                "primary_group": group_info,
                "aces": consolidated_aces,
                "scan_time": datetime.now().isoformat(),
                "success": True
            }

        except Exception as e:
            logger.error(f"Error scanning {folder_path}: {str(e)}", exc_info=True)
            return {
                "path": folder_path,
                "error": str(e),
                "scan_time": datetime.now().isoformat(),
                "success": False
            }

    def scan_directory(self, root_path: str, recursive: bool = True) -> List[Dict]:
        """Scan a directory and optionally its subdirectories for permissions."""
        logger.info(f"Starting directory scan at: {root_path}")
        results = []
        
        try:
            # Scan root directory
            root_permissions = self.get_folder_permissions(root_path)
            results.append(root_permissions)
            
            if recursive:
                for item in os.listdir(root_path):
                    item_path = os.path.join(root_path, item)
                    if os.path.isdir(item_path):
                        try:
                            results.extend(self.scan_directory(item_path, recursive))
                        except Exception as e:
                            logger.error(f"Error scanning subdirectory {item_path}: {str(e)}")
                            results.append({
                                "path": item_path,
                                "error": str(e),
                                "scan_time": datetime.now().isoformat(),
                                "success": False
                            })
                            
        except Exception as e:
            logger.error(f"Error in directory scan: {str(e)}", exc_info=True)
            results.append({
                "path": root_path,
                "error": str(e),
                "scan_time": datetime.now().isoformat(),
                "success": False
            })
            
        return results