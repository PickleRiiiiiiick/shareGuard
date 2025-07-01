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
        
        # SID resolution cache to improve performance
        self.sid_cache = {}
        
        self.group_resolver = GroupResolver()
        logger.info("PermissionScanner initialized with categorized Windows permissions and SID caching")

    def _is_system_account(self, account_name: str) -> bool:
        """Check if the account is a system account."""
        return (account_name in self.system_accounts or 
                any(account_name.startswith(prefix) for prefix in ['NT ', 'BUILTIN\\', 'NT SERVICE\\']))

    def _get_account_type_str(self, account_type: int) -> str:
        """Convert Windows account type to string representation."""
        type_mapping = {
            win32security.SidTypeUser: "User",
            win32security.SidTypeGroup: "Group",
            win32security.SidTypeWellKnownGroup: "WellKnownGroup",
            win32security.SidTypeAlias: "Alias",
            win32security.SidTypeDeletedAccount: "DeletedAccount",
            win32security.SidTypeInvalid: "Invalid",
            win32security.SidTypeUnknown: "Unknown",
            win32security.SidTypeComputer: "Computer"
        }
        # Add SidTypeLabel if available in this pywin32 version
        if hasattr(win32security, 'SidTypeLabel'):
            type_mapping[win32security.SidTypeLabel] = "Label"
        
        return type_mapping.get(account_type, f"Other ({account_type})")

    def _get_trustee_name(self, sid: bytes) -> Dict[str, str]:
        """Convert a security identifier (SID) to a readable name with multiple fallback methods."""
        sid_string = win32security.ConvertSidToStringSid(sid)
        
        # Check cache first
        if sid_string in self.sid_cache:
            logger.debug(f"Using cached SID resolution for {sid_string}")
            return self.sid_cache[sid_string]
        
        # Try multiple resolution methods
        methods = [
            self._lookup_sid_local,
            self._lookup_sid_with_domain,
            self._lookup_well_known_sid,
            self._parse_sid_components
        ]
        
        for method in methods:
            try:
                result = method(sid, sid_string)
                if result and result.get("name") != "Unknown":
                    logger.debug(f"Successfully resolved SID {sid_string} using {method.__name__}")
                    # Cache the successful result
                    self.sid_cache[sid_string] = result
                    return result
            except Exception as e:
                logger.debug(f"Method {method.__name__} failed for SID {sid_string}: {str(e)}")
                continue
        
        # All methods failed - return unknown with SID info
        logger.warning(f"Could not resolve SID {sid_string} using any method")
        unknown_result = {
            "name": "Unknown",
            "domain": "Unknown",
            "sid": sid_string,
            "full_name": f"Unknown SID: {sid_string}",
            "account_type": "Unknown",
            "is_system": False
        }
        
        # Cache the unknown result to avoid repeated failed lookups
        self.sid_cache[sid_string] = unknown_result
        return unknown_result

    def _lookup_sid_local(self, sid: bytes, sid_string: str) -> Dict[str, str]:
        """Try to lookup SID on local system."""
        try:
            name, domain, account_type = win32security.LookupAccountSid(None, sid)
            
            # Additional validation - sometimes LookupAccountSid returns empty strings
            if not name or name.strip() == "":
                raise Exception("Empty name returned from LookupAccountSid")
                
            trustee_info = {
                "name": name,
                "domain": domain or "Unknown",
                "sid": sid_string,
                "full_name": f"{domain}\\{name}" if domain else name,
                "account_type": self._get_account_type_str(account_type)
            }
            trustee_info["is_system"] = self._is_system_account(trustee_info["full_name"])
            logger.debug(f"Local SID lookup successful: {trustee_info['full_name']}")
            return trustee_info
            
        except Exception as e:
            logger.debug(f"Local SID lookup failed for {sid_string}: {str(e)}")
            raise

    def _lookup_sid_with_domain(self, sid: bytes, sid_string: str) -> Dict[str, str]:
        """Try to lookup SID with domain controller if available."""
        if hasattr(self, 'group_resolver') and self.group_resolver.domain_controller:
            try:
                name, domain, account_type = win32security.LookupAccountSid(
                    self.group_resolver.domain_controller, sid
                )
                
                # Additional validation
                if not name or name.strip() == "":
                    raise Exception("Empty name returned from domain LookupAccountSid")
                    
                trustee_info = {
                    "name": name,
                    "domain": domain or self.group_resolver.domain_controller,
                    "sid": sid_string,
                    "full_name": f"{domain}\\{name}" if domain else f"{self.group_resolver.domain_controller}\\{name}",
                    "account_type": self._get_account_type_str(account_type)
                }
                trustee_info["is_system"] = self._is_system_account(trustee_info["full_name"])
                logger.debug(f"Domain SID lookup successful: {trustee_info['full_name']}")
                return trustee_info
                
            except Exception as e:
                logger.debug(f"Domain SID lookup failed for {sid_string}: {str(e)}")
                
        raise Exception("No domain controller available or lookup failed")

    def _lookup_well_known_sid(self, sid: bytes, sid_string: str) -> Dict[str, str]:
        """Handle well-known SIDs that might not resolve through normal lookup."""
        well_known_sids = {
            "S-1-1-0": ("Everyone", ""),
            "S-1-5-32-544": ("Administrators", "BUILTIN"),
            "S-1-5-32-545": ("Users", "BUILTIN"),
            "S-1-5-32-546": ("Guests", "BUILTIN"),
            "S-1-5-32-547": ("Power Users", "BUILTIN"),
            "S-1-5-32-551": ("Backup Operators", "BUILTIN"),
            "S-1-5-18": ("SYSTEM", "NT AUTHORITY"),
            "S-1-5-19": ("LOCAL SERVICE", "NT AUTHORITY"),
            "S-1-5-20": ("NETWORK SERVICE", "NT AUTHORITY"),
            "S-1-5-11": ("Authenticated Users", "NT AUTHORITY"),
            "S-1-5-9": ("Enterprise Domain Controllers", "NT AUTHORITY"),
            "S-1-5-2": ("NETWORK", "NT AUTHORITY"),
            "S-1-5-4": ("INTERACTIVE", "NT AUTHORITY"),
            "S-1-3-0": ("CREATOR OWNER", ""),
            "S-1-3-1": ("CREATOR GROUP", ""),
        }
        
        if sid_string in well_known_sids:
            name, domain = well_known_sids[sid_string]
            trustee_info = {
                "name": name,
                "domain": domain or "NT AUTHORITY",
                "sid": sid_string,
                "full_name": f"{domain}\\{name}" if domain else name,
                "account_type": "WellKnownGroup" if "Group" in name or name in ["Users", "Administrators", "Guests"] else "User"
            }
            trustee_info["is_system"] = True
            return trustee_info
        
        raise Exception("Not a well-known SID")

    def _parse_sid_components(self, sid: bytes, sid_string: str) -> Dict[str, str]:
        """Parse SID components to extract domain and RID information."""
        parts = sid_string.split('-')
        if len(parts) >= 4:
            # Extract RID (last part) and domain identifier
            rid = parts[-1]
            domain_parts = '-'.join(parts[:-1])
            
            # Common RID patterns
            rid_mappings = {
                "500": "Administrator",
                "501": "Guest", 
                "502": "KRBTGT",
                "512": "Domain Admins",
                "513": "Domain Users",
                "514": "Domain Guests",
                "515": "Domain Computers",
                "516": "Domain Controllers",
                "517": "Cert Publishers",
                "518": "Schema Admins",
                "519": "Enterprise Admins",
                "520": "Group Policy Creator Owners",
                "521": "Read-only Domain Controllers",
                "553": "RAS and IAS Servers"
            }
            
            if rid in rid_mappings:
                name = rid_mappings[rid]
                
                # Try to get actual domain name
                domain_name = self._get_domain_name_from_sid(domain_parts)
                
                # Determine account type based on RID
                account_type = "Group" if rid in ["512", "513", "514", "515", "516", "517", "518", "519", "520", "521", "553"] else "User"
                
                trustee_info = {
                    "name": name,
                    "domain": domain_name,
                    "sid": sid_string,
                    "full_name": f"{domain_name}\\{name}",
                    "account_type": account_type
                }
                trustee_info["is_system"] = False
                return trustee_info
        
        raise Exception("Could not parse SID components")

    def _get_domain_name_from_sid(self, domain_sid: str) -> str:
        """Try to resolve domain name from domain SID."""
        try:
            # Try to get domain name using group resolver if available
            if hasattr(self, 'group_resolver') and self.group_resolver.domain_controller:
                return self.group_resolver.domain_controller
            
            # Try to resolve domain using Win32 API
            try:
                import win32net
                import win32netcon
                
                # Try to get domain info
                try:
                    domain_info = win32net.NetGetDCName(None, None)
                    if domain_info:
                        domain_name = domain_info.strip('\\')
                        logger.debug(f"Resolved domain name: {domain_name}")
                        return domain_name
                except Exception:
                    pass
                
                # Try to get workstation info
                try:
                    wksta_info = win32net.NetWkstaGetInfo(None, 100)
                    if wksta_info and 'langroup' in wksta_info:
                        domain_name = wksta_info['langroup']
                        logger.debug(f"Resolved domain from workstation info: {domain_name}")
                        return domain_name
                except Exception:
                    pass
                    
            except ImportError:
                pass
            
            # Try to get local computer's domain
            try:
                import socket
                fqdn = socket.getfqdn()
                if '.' in fqdn:
                    domain = fqdn.split('.', 1)[1].split('.')[0].upper()
                    logger.debug(f"Resolved domain from FQDN: {domain}")
                    return domain
            except Exception:
                pass
            
            # Try alternative methods
            try:
                import os
                domain_env = os.environ.get('USERDOMAIN')
                if domain_env and domain_env not in ['WORKGROUP', 'localhost']:
                    logger.debug(f"Resolved domain from environment: {domain_env}")
                    return domain_env
                    
                # Try COMPUTERNAME environment variable as fallback
                computer_name = os.environ.get('COMPUTERNAME')
                if computer_name:
                    logger.debug(f"Using computer name as domain fallback: {computer_name}")
                    return computer_name
            except Exception:
                pass
                
        except Exception as e:
            logger.debug(f"Could not resolve domain name for SID {domain_sid}: {str(e)}")
        
        # Return a more informative default with SID info
        return f"DOMAIN-{domain_sid.split('-')[-3] if '-' in domain_sid else 'UNKNOWN'}"

    def clear_sid_cache(self):
        """Clear the SID resolution cache."""
        cache_size = len(self.sid_cache)
        self.sid_cache.clear()
        logger.info(f"Cleared SID cache containing {cache_size} entries")

    def get_sid_cache_stats(self) -> Dict[str, int]:
        """Get statistics about the SID cache."""
        total_entries = len(self.sid_cache)
        unknown_entries = sum(1 for entry in self.sid_cache.values() if entry.get("name") == "Unknown")
        resolved_entries = total_entries - unknown_entries
        
        return {
            "total_entries": total_entries,
            "resolved_entries": resolved_entries,
            "unknown_entries": unknown_entries
        }

    def diagnose_sid_issues(self, folder_path: str) -> Dict:
        """Diagnose SID resolution issues for a specific folder."""
        logger.info(f"Diagnosing SID resolution issues for: {folder_path}")
        
        try:
            # Clear cache to get fresh results
            self.clear_sid_cache()
            
            # Get folder permissions
            result = self.get_folder_permissions(folder_path, simplified_system=False)
            
            if not result.get('success'):
                return {"error": "Failed to get folder permissions", "details": result}
            
            aces = result.get('aces', [])
            diagnosis = {
                "folder_path": folder_path,
                "total_aces": len(aces),
                "sid_resolution_summary": {},
                "problematic_sids": [],
                "cache_stats": self.get_sid_cache_stats()
            }
            
            # Analyze each ACE
            for ace in aces:
                trustee = ace.get('trustee', {})
                sid = trustee.get('sid')
                name = trustee.get('name')
                
                if not sid:
                    continue
                    
                # Track resolution success/failure
                if name == "Unknown":
                    diagnosis["problematic_sids"].append({
                        "sid": sid,
                        "full_name": trustee.get('full_name'),
                        "domain": trustee.get('domain'),
                        "account_type": trustee.get('account_type')
                    })
                else:
                    # Successfully resolved
                    resolution_method = "resolved"
                    if sid in diagnosis["sid_resolution_summary"]:
                        diagnosis["sid_resolution_summary"][resolution_method] += 1
                    else:
                        diagnosis["sid_resolution_summary"][resolution_method] = 1
            
            # Add summary counts
            diagnosis["unknown_count"] = len(diagnosis["problematic_sids"])
            diagnosis["resolved_count"] = diagnosis["total_aces"] - diagnosis["unknown_count"]
            
            return diagnosis
            
        except Exception as e:
            logger.error(f"Error during SID diagnosis: {str(e)}")
            return {"error": str(e)}

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

            # Check if inheritance is disabled by looking at the security descriptor control flags
            sd_control = sd.GetSecurityDescriptorControl()
            # SE_DACL_PROTECTED flag indicates that inheritance is disabled
            inheritance_enabled = not (sd_control[0] & win32security.SE_DACL_PROTECTED)
            logger.debug(f"Security descriptor control for {folder_path}: {sd_control[0]}, inheritance_enabled: {inheritance_enabled}")

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
                "inheritance_enabled": inheritance_enabled,
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

    def _permission_string_to_mask(self, permissions: List[str]) -> int:
        """Convert permission strings to Windows access mask."""
        permission_mapping = {
            "read": ntsecuritycon.GENERIC_READ,
            "write": ntsecuritycon.GENERIC_WRITE,
            "execute": ntsecuritycon.GENERIC_EXECUTE,
            "delete": ntsecuritycon.DELETE,
            "modify": ntsecuritycon.GENERIC_WRITE | ntsecuritycon.DELETE,
            "full_control": ntsecuritycon.GENERIC_ALL,
            "list_folder": ntsecuritycon.FILE_LIST_DIRECTORY,
            "create_files": ntsecuritycon.FILE_ADD_FILE,
            "create_folders": ntsecuritycon.FILE_ADD_SUBDIRECTORY,
        }
        
        access_mask = 0
        for permission in permissions:
            if permission.lower() in permission_mapping:
                access_mask |= permission_mapping[permission.lower()]
        
        return access_mask

    def set_folder_permissions(
        self,
        folder_path: str,
        user_or_group: str,
        permissions: List[str],
        access_type: str = "allow"
    ) -> Dict:
        """
        Set permissions for a user or group on a folder.
        
        Args:
            folder_path: Path to the folder
            user_or_group: User or group name (DOMAIN\\USERNAME format)
            permissions: List of permission strings
            access_type: "allow" or "deny"
        """
        logger.info(f"Setting {access_type} permissions for {user_or_group} on {folder_path}: {permissions}")
        
        try:
            if not os.path.exists(folder_path):
                return {"success": False, "error": f"Path does not exist: {folder_path}"}

            # Get the user/group SID
            try:
                if '\\' in user_or_group:
                    domain, username = user_or_group.split('\\', 1)
                    sid, _, _ = win32security.LookupAccountName(domain, username)
                else:
                    sid, _, _ = win32security.LookupAccountName(None, user_or_group)
            except Exception as e:
                return {"success": False, "error": f"Could not resolve user/group: {str(e)}"}

            # Get current security descriptor
            sd = win32security.GetFileSecurity(
                folder_path,
                win32security.DACL_SECURITY_INFORMATION
            )

            # Get current DACL
            dacl = sd.GetSecurityDescriptorDacl()
            if dacl is None:
                dacl = win32security.ACL()

            # Convert permission strings to access mask
            access_mask = self._permission_string_to_mask(permissions)
            if access_mask == 0:
                return {"success": False, "error": "No valid permissions specified"}

            # Determine ACE type
            ace_type = win32security.ACCESS_ALLOWED_ACE_TYPE if access_type == "allow" else win32security.ACCESS_DENIED_ACE_TYPE
            
            # Add the new ACE
            dacl.AddAccessAllowedAce(win32security.ACL_REVISION, access_mask, sid)

            # Set the new DACL
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(folder_path, win32security.DACL_SECURITY_INFORMATION, sd)

            logger.info(f"Successfully set permissions for {user_or_group} on {folder_path}")
            return {
                "success": True,
                "path": folder_path,
                "user_or_group": user_or_group,
                "permissions": permissions,
                "access_type": access_type
            }

        except Exception as e:
            logger.error(f"Error setting permissions: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def remove_folder_permissions(
        self,
        folder_path: str,
        user_or_group: str
    ) -> Dict:
        """
        Remove all permissions for a user or group from a folder.
        
        Args:
            folder_path: Path to the folder
            user_or_group: User or group name (DOMAIN\\USERNAME format)
        """
        logger.info(f"Removing permissions for {user_or_group} from {folder_path}")
        
        try:
            if not os.path.exists(folder_path):
                return {"success": False, "error": f"Path does not exist: {folder_path}"}

            # Get the user/group SID
            try:
                if '\\' in user_or_group:
                    domain, username = user_or_group.split('\\', 1)
                    sid, _, _ = win32security.LookupAccountName(domain, username)
                else:
                    sid, _, _ = win32security.LookupAccountName(None, user_or_group)
            except Exception as e:
                return {"success": False, "error": f"Could not resolve user/group: {str(e)}"}

            # Get current security descriptor
            sd = win32security.GetFileSecurity(
                folder_path,
                win32security.DACL_SECURITY_INFORMATION
            )

            # Get current DACL
            dacl = sd.GetSecurityDescriptorDacl()
            if dacl is None:
                return {"success": True, "message": "No permissions to remove"}

            # Create new DACL without the specified user's ACEs
            new_dacl = win32security.ACL()
            
            for ace_index in range(dacl.GetAceCount()):
                ace = dacl.GetAce(ace_index)
                ace_sid = ace[2]
                
                # Only add ACE if it's not for the user we're removing
                if not win32security.EqualSid(ace_sid, sid):
                    new_dacl.AddAccessAllowedAce(ace[0][1], ace[1], ace_sid)

            # Set the new DACL
            sd.SetSecurityDescriptorDacl(1, new_dacl, 0)
            win32security.SetFileSecurity(folder_path, win32security.DACL_SECURITY_INFORMATION, sd)

            logger.info(f"Successfully removed permissions for {user_or_group} from {folder_path}")
            return {
                "success": True,
                "path": folder_path,
                "user_or_group": user_or_group,
                "message": "Permissions removed successfully"
            }

        except Exception as e:
            logger.error(f"Error removing permissions: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}