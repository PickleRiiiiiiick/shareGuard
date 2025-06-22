# src/scanner/group_resolver.py

import win32security
import win32net
import win32netcon
import win32com.client
import pywintypes
from typing import Dict, List, Set, Optional
from datetime import datetime, timedelta
import logging
from ..utils.logger import setup_logger
import socket

logger = setup_logger('group_resolver')

class GroupResolver:
    """Universal group resolver supporting multiple domain environments."""

    def __init__(self, domain_controller: str = None):
        """
        Initialize resolver with optional domain controller.

        Args:
            domain_controller: Optional domain controller address. If None, auto-discovers.
        """
        self._cache = {
            'groups': {},           # Cache for group details
            'users': {},            # Cache for user group memberships
            'paths': {},            # Cache for access paths
            'memberships': {},      # Cache for group memberships
            'group_members': {},    # Cache for direct group members
            'sid_to_account': {},   # Cache for SID resolutions
            'domain_info': {}       # Cache for domain information
        }

        self._cache_times = {}
        self.cache_ttl = 3600  # 1 hour default TTL
        self.max_depth = 10    # Maximum depth for nested group resolution
        self.query_timeout = 30 # Timeout for AD queries

        # Initialize domain controller info
        self.domain_controller = domain_controller
        self.domain_info = {}

        # System accounts configuration
        self.system_accounts = {
            'NT AUTHORITY\\SYSTEM',
            'NT AUTHORITY\\LOCAL SERVICE',
            'NT AUTHORITY\\NETWORK SERVICE',
            'NT AUTHORITY\\Authenticated Users',
            'BUILTIN\\Administrators',
            'BUILTIN\\Users',
            'BUILTIN\\Power Users',
            'NT SERVICE\\',
            'CREATOR OWNER'
        }

        self._initialize_domain_info()
        logger.info("GroupResolver initialized with TTL: %d seconds", self.cache_ttl)

    def _initialize_domain_info(self):
        """Initialize domain controller and forest information."""
        try:
            if not self.domain_controller:
                # Try to auto-discover domain controller
                try:
                    dc_info = win32net.NetGetDCName(None, None)
                    self.domain_controller = dc_info.strip('\\')
                except Exception as e:
                    logger.warning(f"Could not auto-discover DC: {str(e)}")
                    # Try getting local computer's domain
                    try:
                        domain = win32security.GetDomainName()
                        if domain:
                            self.domain_controller = domain
                    except Exception as de:
                        logger.warning(f"Could not get domain name: {str(de)}")

            if self.domain_controller:
                logger.info(f"Using domain controller: {self.domain_controller}")
                self.domain_info = {
                    'name': self.domain_controller,
                    'forest': None,
                    'domain_mode': None,
                    'schema_master': None
                }

                # Try to get additional domain info using Win32 API
                try:
                    domain_info = win32net.NetGetDCName(None, None)
                    if domain_info:
                        self.domain_info['forest'] = win32net.NetGetAnyDCName(None, None)
                except Exception as e:
                    logger.debug(f"Could not get additional domain info: {str(e)}")

        except Exception as e:
            logger.warning(f"Error during domain initialization: {str(e)}")

    def _is_cache_valid(self, cache_type: str, key: str) -> bool:
        """Check if cached data is still valid."""
        if key in self._cache_times:
            cache_time = self._cache_times.get(key)
            if cache_time and (datetime.now() - cache_time) < timedelta(seconds=self.cache_ttl):
                logger.debug(f"Cache hit for {cache_type}: {key}")
                return True
        return False

    def _get_cached(self, cache_type: str, key: str) -> Optional[Dict]:
        """Get data from cache if valid."""
        if cache_type in self._cache and self._is_cache_valid(cache_type, key):
            return self._cache[cache_type].get(key)
        return None

    def _set_cached(self, cache_type: str, key: str, value: Dict) -> None:
        """Store data in cache with timestamp."""
        if cache_type in self._cache:
            self._cache[cache_type][key] = value
            self._cache_times[key] = datetime.now()
            logger.debug(f"Cached {cache_type}: {key}")

    def _is_system_account(self, account_name: str) -> bool:
        """Check if the account is a system account."""
        is_system = (account_name in self.system_accounts or 
                     any(account_name.startswith(prefix) for prefix in ['NT ', 'BUILTIN\\', 'NT SERVICE\\']))
        logger.debug(f"Account {account_name} is system: {is_system}")
        return is_system

    def _get_account_details(self, name: str, domain: str) -> Dict[str, str]:
        """Get detailed account information including SID and type."""
        try:
            sid, domain, account_type = win32security.LookupAccountName(domain, name)
            sid_string = win32security.ConvertSidToStringSid(sid)

            details = {
                'name': name,
                'domain': domain,
                'sid': sid_string,
                'full_name': f"{domain}\\{name}",
                'type': self._get_account_type_str(account_type),
                'is_system': self._is_system_account(f"{domain}\\{name}")
            }

            logger.debug(f"Retrieved account details for {domain}\\{name}")
            return details
        except pywintypes.error as e:
            logger.warning(f"Failed to get account details for {domain}\\{name}: {str(e)}")
            return {
                'name': name,
                'domain': domain,
                'sid': None,
                'full_name': f"{domain}\\{name}",
                'type': 'Unknown',
                'is_system': self._is_system_account(f"{domain}\\{name}")
            }

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

    def _get_group_members_multi_provider(self, group_name: str, domain: str) -> List[Dict]:
        """Get group members using multiple providers with fallback."""
        members = []
        cache_key = f"{domain}\\{group_name}"

        # Check cache first
        cached_members = self._get_cached('group_members', cache_key)
        if cached_members is not None:
            return cached_members

        # Try ADSI first, then fall back to Win32Net
        try:
            members = self._get_members_adsi(group_name, domain)
        except Exception as e:
            logger.debug(f"ADSI method failed for {group_name}: {str(e)}")
            try:
                members = self._get_members_win32net(group_name, domain)
            except Exception as e2:
                logger.warning(f"All member resolution methods failed for {domain}\\{group_name}. Error: {str(e2)}")

        # Cache the results even if empty
        self._set_cached('group_members', cache_key, members)
        logger.info(f"Found {len(members)} members for group {cache_key}")

        return members

    def _get_members_adsi(self, group_name: str, domain: str) -> List[Dict]:
        """Get group members using ADSI."""
        members = []

        try:
            # Try WinNT provider
            adsi_paths = [
                f"WinNT://{domain}/{group_name},group",  # Try domain path
                f"WinNT://localhost/{group_name},group"  # Try local path
            ]

            success = False
            last_error = None

            for adsi_path in adsi_paths:
                try:
                    logger.debug(f"Attempting ADSI connection to: {adsi_path}")
                    adsi_group = win32com.client.GetObject(adsi_path)

                    # Attempt to get members
                    try:
                        member_collection = adsi_group.Members()
                        for member in member_collection:
                            try:
                                member_name = member.Name
                                member_path = member.AdsPath

                                # Parse domain from AdsPath if available
                                member_domain = domain
                                if '/' in member_path:
                                    path_parts = member_path.split('/')
                                    if len(path_parts) > 2:
                                        member_domain = path_parts[2]

                                member_info = self._get_account_details(member_name, member_domain)
                                if member_info not in members:  # Avoid duplicates
                                    members.append(member_info)
                                    logger.debug(f"Found member via ADSI: {member_info['full_name']}")

                            except Exception as member_err:
                                logger.warning(f"Error processing ADSI member: {str(member_err)}")
                                continue

                        success = True
                        break  # Break if successful

                    except Exception as members_err:
                        last_error = str(members_err)
                        logger.debug(f"Failed to get members from {adsi_path}: {last_error}")
                        continue

                except Exception as path_err:
                    last_error = str(path_err)
                    logger.debug(f"Failed to connect to {adsi_path}: {last_error}")
                    continue

            if not success and last_error:
                logger.warning(f"All ADSI paths failed for {domain}\\{group_name}. Last error: {last_error}")
                raise Exception(f"ADSI access failed: {last_error}")

            logger.debug(f"Found {len(members)} members via ADSI for {domain}\\{group_name}")

        except Exception as e:
            logger.warning(f"ADSI access failed for {domain}\\{group_name}: {str(e)}")
            raise

        return members

    def _get_members_win32net(self, group_name: str, domain: str) -> List[Dict]:
        """Get group members using Win32Net API."""
        members = []
        last_error = None

        try:
            # Try as domain group first
            try:
                resume = 0
                while True:
                    data, total, resume = win32net.NetGroupGetUsers(domain, group_name, 1)
                    for member in data:
                        try:
                            member_info = self._get_account_details(member['name'], domain)
                            if member_info not in members:  # Avoid duplicates
                                members.append(member_info)
                                logger.debug(f"Found domain group member: {member_info['full_name']}")
                        except Exception as e:
                            logger.warning(f"Error processing group member: {str(e)}")
                    if not resume:
                        break
            except win32net.error as e:
                last_error = str(e)
                logger.debug(f"NetGroupGetUsers failed: {last_error}")

            # If domain group failed or no members found, try as local group
            if not members:
                try:
                    resume = 0
                    while True:
                        data, total, resume = win32net.NetLocalGroupGetMembers(None, group_name, 1)
                        for member in data:
                            try:
                                name = member['name']
                                if '\\' in name:
                                    mem_domain, mem_name = name.split('\\')
                                else:
                                    mem_domain, mem_name = domain, name

                                member_info = self._get_account_details(mem_name, mem_domain)
                                if member_info not in members:  # Avoid duplicates
                                    members.append(member_info)
                                    logger.debug(f"Found local group member: {member_info['full_name']}")
                            except Exception as e:
                                logger.warning(f"Error processing local member: {str(e)}")
                        if not resume:
                            break
                except win32net.error as e:
                    if last_error:
                        logger.warning(f"Both domain and local group access failed. Domain error: {last_error}, Local error: {str(e)}")
                    else:
                        logger.warning(f"Local group access failed: {str(e)}")
                    raise Exception("Failed to get group members through Win32Net API")

        except Exception as e:
            logger.warning(f"Win32Net access failed: {str(e)}")
            raise

        return members

    def _get_user_groups(self, username: str, domain: str) -> List[Dict]:
        """Get all groups a user belongs to using multiple methods."""
        cache_key = f"{domain}\\{username}"
        cached_groups = self._get_cached('users', cache_key)
        if cached_groups is not None:
            return cached_groups

        if self._is_system_account(cache_key):
            return []

        logger.info(f"Getting groups for user: {cache_key}")
        groups = []
        last_error = None

        # Try ADSI first
        try:
            user_path = f"WinNT://{domain}/{username},user"
            logger.debug(f"Attempting ADSI connection to: {user_path}")

            adsi_user = win32com.client.GetObject(user_path)
            groups_collection = adsi_user.Groups()

            for group in groups_collection:
                try:
                    group_name = group.Name
                    group_path = group.AdsPath
                    group_domain = domain

                    if '/' in group_path:
                        group_domain = group_path.split('/')[2]

                    group_info = self._get_account_details(group_name, group_domain)
                    if group_info not in groups:  # Avoid duplicates
                        groups.append(group_info)
                        logger.debug(f"Found group membership: {group_info['full_name']}")

                except Exception as e:
                    logger.warning(f"Error processing group for {username}: {str(e)}")

        except Exception as e:
            last_error = str(e)
            logger.warning(f"ADSI lookup failed for {username}: {str(e)}")

        # If ADSI failed or found no groups, try Win32Net
        if not groups:
            try:
                # Try domain groups
                try:
                    groups_data = win32net.NetUserGetGroups(domain, username)
                    for group_name, _ in groups_data:
                        group_info = self._get_account_details(group_name, domain)
                        if group_info not in groups:  # Avoid duplicates
                            groups.append(group_info)
                            logger.debug(f"Found domain group: {group_info['full_name']}")
                except win32net.error as e:
                    logger.debug(f"NetUserGetGroups failed: {str(e)}")

                # Try local groups
                try:
                    local_groups = win32net.NetUserGetLocalGroups(None, username)
                    for group_name in local_groups:
                        if '\\' in group_name:
                            group_domain, group_name = group_name.split('\\')
                        else:
                            group_domain = domain

                        group_info = self._get_account_details(group_name, group_domain)
                        if group_info not in groups:  # Avoid duplicates
                            groups.append(group_info)
                            logger.debug(f"Found local group: {group_info['full_name']}")
                except win32net.error as e:
                    logger.debug(f"NetUserGetLocalGroups failed: {str(e)}")

            except Exception as e:
                if last_error:
                    logger.error(f"Both ADSI and Win32Net failed. ADSI error: {last_error}, Win32Net error: {str(e)}")
                else:
                    logger.error(f"Win32Net lookup failed: {str(e)}")

        # Cache results even if empty
        self._set_cached('users', cache_key, groups)
        logger.info(f"Found {len(groups)} groups for user {cache_key}")

        return groups

    def get_access_paths(self, trustee: Dict[str, str]) -> Dict:
        """
        Build complete access paths for a trustee with enhanced group information.

        Args:
            trustee: Dictionary containing trustee information
                     Must include 'name', 'domain', and 'full_name' keys

        Returns:
            Dictionary containing access path information including:
            - trustee: Original trustee info
            - direct_access: Whether this is direct access
            - group_paths: List of nested group paths
            - nested_level: Depth of nesting
            - group_memberships: List of group members
        """
        try:
            cache_key = trustee['full_name']
            cached_paths = self._get_cached('paths', cache_key)
            if cached_paths is not None:
                return cached_paths

            logger.info(f"Building access paths for: {cache_key}")

            access_paths = {
                'trustee': trustee,
                'direct_access': True,
                'group_paths': [],
                'nested_level': 0,
                'group_memberships': []
            }

            if not self._is_system_account(trustee['full_name']):
                try:
                    account_details = self._get_account_details(trustee['name'], trustee['domain'])
                    account_type = account_details['type']
                    logger.debug(f"Processing trustee {trustee['full_name']} of type {account_type}")

                    if account_type in ['Group', 'WellKnownGroup', 'Alias']:
                        # Get direct members for groups
                        direct_members = self._get_group_members_multi_provider(
                            trustee['name'],
                            trustee['domain']
                        )
                        access_paths['group_memberships'] = direct_members
                        logger.debug(f"Found {len(direct_members)} direct members")

                        # Process nested groups
                        nested_groups = [m for m in direct_members 
                                         if m['type'] in ['Group', 'WellKnownGroup', 'Alias']]
                        for group in nested_groups:
                            nested_path = self._trace_group_path(group)
                            if nested_path:
                                access_paths['group_paths'].append(nested_path)

                    elif account_type in ['User', 'Unknown']:
                        # Get group memberships for users
                        user_groups = self._get_user_groups(trustee['name'], trustee['domain'])
                        logger.debug(f"Found {len(user_groups)} groups for user")

                        for group in user_groups:
                            group_path = self._trace_group_path(group)
                            if group_path:
                                access_paths['group_paths'].append(group_path)
                                # Get members of each group
                                group_members = self._get_group_members_multi_provider(
                                    group['name'],
                                    group['domain']
                                )
                                for member in group_members:
                                    if member not in access_paths['group_memberships']:
                                        access_paths['group_memberships'].append(member)

                except Exception as e:
                    logger.error(f"Error processing {trustee['full_name']}: {str(e)}", exc_info=True)

            # Cache the results
            self._set_cached('paths', cache_key, access_paths)
            return access_paths

        except Exception as e:
            logger.error(f"Error building access paths for {trustee['full_name']}: {str(e)}", 
                         exc_info=True)
            # Return a basic structure in case of error
            return {
                'trustee': trustee,
                'direct_access': True,
                'group_paths': [],
                'nested_level': 0,
                'group_memberships': []
            }

    def _trace_group_path(self, group: Dict[str, str], visited: Optional[Set[str]] = None, 
                          current_depth: int = 0) -> Optional[Dict]:
        """Recursively trace group membership path."""
        if visited is None:
            visited = set()

        if current_depth >= self.max_depth:
            logger.warning(f"Max depth reached while tracing group: {group['full_name']}")
            return None

        group_key = group['full_name']
        if group_key in visited:
            logger.debug(f"Cycle detected in group path: {group_key}")
            return None

        visited.add(group_key)
        logger.debug(f"Tracing group path for: {group_key} (depth: {current_depth})")

        try:
            path = {
                'group': group,
                'member_groups': [],
                'nested_level': current_depth,
                'members': []
            }

            if not self._is_system_account(group_key):
                try:
                    path['members'] = self._get_group_members_multi_provider(
                        group['name'],
                        group['domain']
                    )

                    # Process nested groups
                    nested_groups = [m for m in path['members'] 
                                     if m['type'] in ['Group', 'WellKnownGroup', 'Alias']]

                    for member in nested_groups:
                        nested_path = self._trace_group_path(
                            member, 
                            visited.copy(), 
                            current_depth + 1
                        )
                        if nested_path:
                            path['member_groups'].append(nested_path)
                            path['nested_level'] = max(
                                path['nested_level'],
                                nested_path['nested_level'] + 1
                            )

                except Exception as e:
                    logger.error(f"Error getting members for {group_key}: {str(e)}")

            return path

        except Exception as e:
            logger.error(f"Error tracing group path for {group_key}: {str(e)}", 
                         exc_info=True)
            return None

    def get_group_members(self, group_name: str, domain: str, include_nested: bool = True) -> Dict:
        """
        Public method to get group members with optional nested group resolution.
        
        Args:
            group_name: Name of the group
            domain: Domain of the group
            include_nested: Whether to include nested group members
            
        Returns:
            Dict containing group members and nested structure
        """
        logger.info(f"Getting members for group {domain}\\{group_name}")
        
        try:
            # Get direct members
            direct_members = self._get_group_members_multi_provider(group_name, domain)
            
            result = {
                'group_name': group_name,
                'domain': domain,
                'full_name': f"{domain}\\{group_name}",
                'direct_members': direct_members,
                'nested_groups': [],
                'all_members': direct_members.copy() if direct_members else [],
                'total_direct_members': len(direct_members) if direct_members else 0,
                'total_all_members': len(direct_members) if direct_members else 0
            }
            
            if include_nested and direct_members:
                # Find nested groups
                nested_groups = [m for m in direct_members 
                               if m.get('type', '').lower() in ['group', 'wellknowngroup', 'alias']]
                
                for nested_group in nested_groups:
                    try:
                        nested_result = self.get_group_members(
                            nested_group['name'], 
                            nested_group['domain'], 
                            include_nested=True
                        )
                        result['nested_groups'].append(nested_result)
                        
                        # Add nested members to all_members (avoiding duplicates)
                        for member in nested_result['all_members']:
                            if not any(m.get('sid') == member.get('sid') for m in result['all_members']):
                                result['all_members'].append(member)
                                
                    except Exception as e:
                        logger.warning(f"Error resolving nested group {nested_group['name']}: {str(e)}")
                
                result['total_all_members'] = len(result['all_members'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting group members for {domain}\\{group_name}: {str(e)}")
            return {
                'group_name': group_name,
                'domain': domain,
                'full_name': f"{domain}\\{group_name}",
                'error': str(e),
                'direct_members': [],
                'nested_groups': [],
                'all_members': [],
                'total_direct_members': 0,
                'total_all_members': 0
            }

    def clear_cache(self, cache_type: Optional[str] = None):
        """
        Clear resolver cache.

        Args:
            cache_type: Optional specific cache to clear. If None, clears all caches.
        """
        try:
            if cache_type:
                if cache_type in self._cache:
                    self._cache[cache_type].clear()
                    if cache_type in self._cache_times:
                        self._cache_times[cache_type].clear()
                    logger.info(f"Cleared {cache_type} cache")
            else:
                self._cache = {
                    'groups': {},
                    'users': {},
                    'paths': {},
                    'memberships': {},
                    'group_members': {},
                    'sid_to_account': {},
                    'domain_info': {}
                }
                self._cache_times = {}
                logger.info("All resolver caches cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")

    def __str__(self) -> str:
        """String representation of the resolver."""
        return f"GroupResolver(dc={self.domain_controller}, cache_ttl={self.cache_ttl}s)"

    def __repr__(self) -> str:
        """Detailed string representation of the resolver."""
        return f"GroupResolver(dc={self.domain_controller}, cache_ttl={self.cache_ttl}s, max_depth={self.max_depth})"
