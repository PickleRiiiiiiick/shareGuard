# src/scanner/group_resolver.py
import win32security
import win32net
import win32netcon
import pywintypes
from typing import Dict, List, Set, Optional
import logging
from ..utils.logger import setup_logger

logger = setup_logger('group_resolver')

class GroupResolver:
    def __init__(self):
        # Initialize caches
        self._cache = {
            'groups': {},
            'users': {},
            'paths': {},
            'memberships': {},
            'group_members': {},
            'sid_to_account': {}
        }
        
        # Define system account identifiers
        self.system_accounts = {
            'NT AUTHORITY\\SYSTEM',
            'NT AUTHORITY\\Authenticated Users',
            'BUILTIN\\Administrators',
            'BUILTIN\\Users',
            'BUILTIN\\Power Users',
            'NT SERVICE\\',
            'CREATOR OWNER'
        }
        logger.info("GroupResolver initialized")

    def _is_system_account(self, account_name: str) -> bool:
        """Check if the account is a system account."""
        return (account_name in self.system_accounts or 
                any(account_name.startswith(prefix) for prefix in ['NT ', 'BUILTIN\\', 'NT SERVICE\\']))

    def _get_account_type(self, name: str, domain: str) -> str:
        """Determine if account is a user or group."""
        try:
            sid, domain, account_type = win32security.LookupAccountName(domain, name)
            if account_type == win32security.SidTypeUser:
                return "User"
            elif account_type == win32security.SidTypeGroup:
                return "Group"
            elif account_type == win32security.SidTypeWellKnownGroup:
                return "WellKnownGroup"
            elif account_type == win32security.SidTypeAlias:
                return "Alias"
            else:
                return f"Other ({account_type})"
        except pywintypes.error:
            return "Unknown"

    def _get_account_by_sid(self, sid: bytes) -> Dict[str, str]:
        """Convert a security identifier (SID) to account information."""
        try:
            sid_string = win32security.ConvertSidToStringSid(sid)
            if sid_string in self._cache['sid_to_account']:
                return self._cache['sid_to_account'][sid_string]

            name, domain, _ = win32security.LookupAccountSid(None, sid)
            account_info = {
                "name": name,
                "domain": domain,
                "sid": sid_string,
                "full_name": f"{domain}\\{name}"
            }
            self._cache['sid_to_account'][sid_string] = account_info
            return account_info
        except Exception as e:
            logger.warning(f"Could not resolve SID: {str(e)}")
            try:
                sid_string = win32security.ConvertSidToStringSid(sid)
                return {
                    "name": "Unknown",
                    "domain": "Unknown",
                    "sid": sid_string,
                    "full_name": f"Unknown SID: {sid_string}"
                }
            except:
                return {
                    "name": "Unknown",
                    "domain": "Unknown",
                    "sid": "Unknown",
                    "full_name": "Unknown Account"
                }

    def _get_group_members_recursive(self, group_name: str, domain: str, visited: Optional[Set[str]] = None) -> List[Dict]:
        """Get all members of a group recursively, including nested groups."""
        if visited is None:
            visited = set()
            
        cache_key = f"{domain}\\{group_name}"
        if cache_key in self._cache['group_members']:
            return self._cache['group_members'][cache_key]
            
        if cache_key in visited:
            return []
            
        visited.add(cache_key)
        members = []
        
        try:
            resume = 0
            while True:
                try:
                    # Get immediate members
                    data, total, resume = win32net.NetLocalGroupGetMembers(
                        domain if domain != 'BUILTIN' else None,
                        group_name, 
                        2, 
                        resume,
                        512
                    )
                    
                    for member in data:
                        if 'domainandname' in member:
                            member_domain, member_name = member['domainandname'].split('\\')
                            account_type = self._get_account_type(member_name, member_domain)
                            
                            member_info = {
                                'name': member_name,
                                'domain': member_domain,
                                'type': account_type,
                                'full_name': member['domainandname'],
                                'nested_groups': []
                            }
                            
                            # If member is a group, get its members recursively
                            if account_type in ['Group', 'WellKnownGroup']:
                                nested_members = self._get_group_members_recursive(
                                    member_name,
                                    member_domain,
                                    visited.copy()
                                )
                                member_info['nested_groups'] = nested_members
                                
                            members.append(member_info)
                            
                except win32net.error:
                    break
                    
                if not resume:
                    break
                    
        except Exception as e:
            if not self._is_system_account(cache_key):
                logger.warning(f"Error getting members for group {group_name}: {str(e)}")
                
        self._cache['group_members'][cache_key] = members
        return members

    def _get_group_members(self, group_name: str, domain: str = None) -> List[Dict]:
        """Get direct members of a group."""
        cache_key = f"{domain}\\{group_name}"
        if cache_key in self._cache['memberships']:
            return self._cache['memberships'][cache_key]

        members = []
        if not self._is_system_account(cache_key):
            try:
                resume = 0
                server = None if domain == 'BUILTIN' else domain
                
                while True:
                    try:
                        data, total, resume = win32net.NetLocalGroupGetMembers(
                            server, group_name, 2, resume, 512
                        )
                        
                        for member in data:
                            if 'domainandname' in member:
                                member_domain, member_name = member['domainandname'].split('\\')
                                account_type = self._get_account_type(member_name, member_domain)
                                
                                member_info = {
                                    'name': member_name,
                                    'domain': member_domain,
                                    'type': account_type,
                                    'full_name': member['domainandname']
                                }
                                members.append(member_info)
                                
                    except win32net.error as e:
                        logger.warning(f"NetLocalGroupGetMembers error: {str(e)}")
                        break

                    if not resume:
                        break

            except Exception as e:
                if not self._is_system_account(cache_key):
                    logger.warning(f"Error getting members for group {group_name}: {str(e)}")

        self._cache['memberships'][cache_key] = members
        return members

    def _get_user_groups(self, username: str, domain: str) -> List[Dict]:
        """Get all groups a user belongs to."""
        cache_key = f"{domain}\\{username}"
        if cache_key in self._cache['users']:
            return self._cache['users'][cache_key]

        # Skip group resolution for system accounts
        if self._is_system_account(cache_key):
            return []

        groups = []
        try:
            # Get domain groups
            try:
                domain_groups = win32net.NetUserGetGroups(None, username)
                for group_name, _ in domain_groups:
                    groups.append({
                        'name': group_name,
                        'domain': domain,
                        'type': 'Group',
                        'full_name': f"{domain}\\{group_name}"
                    })
            except win32net.error as e:
                logger.debug(f"NetUserGetGroups error: {str(e)}")

            # Get local groups
            try:
                local_groups = win32net.NetUserGetLocalGroups(None, f"{domain}\\{username}", 0)
                for group in local_groups:
                    if '\\' in group:
                        group_domain, group_name = group.split('\\')
                    else:
                        group_domain, group_name = domain, group
                    groups.append({
                        'name': group_name,
                        'domain': group_domain,
                        'type': 'Group',
                        'full_name': f"{group_domain}\\{group_name}"
                    })
            except win32net.error as e:
                logger.debug(f"NetUserGetLocalGroups error: {str(e)}")

        except Exception as e:
            if not self._is_system_account(cache_key):
                logger.warning(f"Error getting groups for user {username}: {str(e)}")

        self._cache['users'][cache_key] = groups
        return groups

    def get_access_paths(self, trustee: Dict[str, str]) -> Dict:
        """Build complete access paths for a trustee with enhanced group information."""
        cache_key = trustee['full_name']
        if cache_key in self._cache['paths']:
            return self._cache['paths'][cache_key]

        access_paths = {
            'trustee': trustee,
            'direct_access': True,
            'group_paths': [],
            'nested_level': 0,
            'group_memberships': [],
            'is_system_account': self._is_system_account(trustee['full_name'])
        }

        # Skip detailed resolution for system accounts if configured
        if not access_paths['is_system_account']:
            # Get account type
            account_type = self._get_account_type(trustee['name'], trustee['domain'])
            
            # If it's a group, get its members
            if account_type in ['Group', 'WellKnownGroup', 'Alias']:
                group_members = self._get_group_members_recursive(
                    trustee['name'],
                    trustee['domain']
                )
                access_paths['group_memberships'] = group_members
                
            # If it's a user, get their groups and process each group's members
            elif account_type in ['User', 'Unknown']:
                user_groups = self._get_user_groups(trustee['name'], trustee['domain'])
                for group in user_groups:
                    group_path = self._trace_group_path(group)
                    if group_path:
                        access_paths['group_paths'].append(group_path)
                        # Get members of each group
                        group_members = self._get_group_members_recursive(
                            group['name'],
                            group['domain']
                        )
                        group_path['members'] = group_members
                        access_paths['nested_level'] = max(
                            access_paths['nested_level'],
                            group_path['nested_level']
                        )

        self._cache['paths'][cache_key] = access_paths
        return access_paths

    def _trace_group_path(self, group: Dict[str, str], visited: Optional[Set[str]] = None) -> Optional[Dict]:
        """Recursively trace group membership path with enhanced member information."""
        if visited is None:
            visited = set()

        group_key = group['full_name']
        if group_key in visited:
            return None

        visited.add(group_key)
        
        path = {
            'group': group,
            'member_groups': [],
            'nested_level': 0,
            'members': [],
            'is_system_account': self._is_system_account(group_key)
        }

        if not path['is_system_account']:
            # Get direct members
            path['members'] = self._get_group_members_recursive(
                group['name'],
                group['domain']
            )
            
            # Process nested groups
            members = self._get_group_members(group['name'], group['domain'])
            for member in members:
                if member['type'] in ['Group', 'WellKnownGroup']:
                    nested_path = self._trace_group_path(member, visited.copy())
                    if nested_path:
                        path['member_groups'].append(nested_path)
                        path['nested_level'] = max(
                            path['nested_level'],
                            nested_path['nested_level'] + 1
                        )

        return path

    def clear_cache(self):
        """Clear the resolver cache."""
        self._cache = {
            'groups': {},
            'users': {},
            'paths': {},
            'memberships': {},
            'group_members': {},
            'sid_to_account': {}
        }
        logger.info("GroupResolver cache cleared")