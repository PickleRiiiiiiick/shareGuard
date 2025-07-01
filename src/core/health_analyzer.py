# src/core/health_analyzer.py
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import json
from dataclasses import dataclass
from sqlalchemy.orm import Session

from src.db.models.health import Issue, HealthScan, HealthMetrics, HealthScoreHistory, IssueSeverity, IssueType, IssueStatus
from src.db.database import SessionLocal
from src.core.scanner import ShareGuardScanner

logger = logging.getLogger(__name__)


@dataclass
class HealthAnalysisConfig:
    """Configuration for health analysis."""
    max_ace_count_threshold: int = 50
    max_direct_user_aces: int = 5
    critical_groups: List[str] = None
    score_weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.critical_groups is None:
            self.critical_groups = [
                "Domain Admins",
                "Enterprise Admins", 
                "Administrators",
                "BUILTIN\\Administrators",
                "Everyone"
            ]
        
        if self.score_weights is None:
            self.score_weights = {
                IssueType.BROKEN_INHERITANCE.value: 15.0,
                IssueType.DIRECT_USER_ACE.value: 10.0,
                IssueType.ORPHANED_SID.value: 5.0,
                IssueType.EXCESSIVE_ACE_COUNT.value: 20.0,
                IssueType.CONFLICTING_DENY_ORDER.value: 25.0,
                IssueType.OVER_PERMISSIVE_GROUPS.value: 25.0
            }


class HealthAnalyzer:
    """Analyzes ACL configurations and calculates security health scores."""
    
    def __init__(self, config: HealthAnalysisConfig = None):
        self.config = config or HealthAnalysisConfig()
        self.scanner = ShareGuardScanner()
        logger.info("Health analyzer initialized")
    
    def run_health_scan(self, target_paths: List[str]) -> int:
        """Run a complete health analysis scan."""
        db = SessionLocal()
        try:
            # Create health scan record
            scan = HealthScan(
                start_time=datetime.now(timezone.utc),
                status="running",
                total_paths=len(target_paths),
                scan_parameters={"target_paths": target_paths}
            )
            db.add(scan)
            db.commit()
            db.refresh(scan)
            
            logger.info(f"Started health scan {scan.id} for {len(target_paths)} paths")
            logger.info(f"Target paths to analyze: {target_paths}")
            
            all_issues = []
            processed_paths = 0
            
            for path in target_paths:
                try:
                    # First check if we have existing scan data
                    from src.db.models import ScanResult
                    existing_scan = db.query(ScanResult).filter(
                        ScanResult.path == path,
                        ScanResult.success == True
                    ).order_by(ScanResult.scan_time.desc()).first()
                    
                    if existing_scan and existing_scan.permissions:
                        # Use existing scan data
                        logger.info(f"Using existing scan data for {path}")
                        # Parse JSON if stored as string
                        import json
                        if isinstance(existing_scan.permissions, str):
                            try:
                                scan_result = json.loads(existing_scan.permissions)
                                scan_result['success'] = True  # Mark as successful since it's valid stored data
                            except json.JSONDecodeError:
                                logger.error(f"Failed to parse stored permissions JSON for {path}")
                                scan_result = {'success': False, 'error': 'Invalid JSON in stored scan data'}
                        else:
                            scan_result = existing_scan.permissions
                        # Ensure it has the expected structure
                        if not isinstance(scan_result, dict):
                            scan_result = {'success': False, 'error': 'Invalid scan data format'}
                    else:
                        # Scan the path if no existing data
                        logger.warning(f"No existing scan data found for {path}")
                        logger.info(f"Attempting to scan {path} now")
                        scan_result = self.scanner.scan_path(path)
                        
                        # Store the new scan result in database for future use
                        if scan_result.get('success', False):
                            from src.db.models import ScanResult
                            new_scan_result = ScanResult(
                                path=path,
                                scan_time=datetime.now(timezone.utc),
                                success=True,
                                permissions=scan_result,  # Store the entire result
                                error_message=None
                            )
                            db.add(new_scan_result)
                            logger.info(f"Stored new scan result for {path}")
                        else:
                            # Also store failed scans to avoid repeated attempts
                            from src.db.models import ScanResult
                            new_scan_result = ScanResult(
                                path=path,
                                scan_time=datetime.now(timezone.utc),
                                success=False,
                                permissions=None,
                                error_message=scan_result.get('error', 'Unknown scan error')
                            )
                            db.add(new_scan_result)
                            logger.warning(f"Stored failed scan result for {path}")
                    
                    if scan_result.get('success', False):
                        # Analyze the scan result for issues
                        logger.info(f"Analyzing scan result for {path}")
                        logger.info(f"Scan result keys for {path}: {list(scan_result.keys())}")
                        
                        # Log inheritance information specifically
                        if 'permissions' in scan_result:
                            perms = scan_result['permissions']
                            if isinstance(perms, dict):
                                logger.info(f"Permissions structure for {path}: {list(perms.keys())}")
                                logger.info(f"Inheritance enabled for {path}: {perms.get('inheritance_enabled', 'NOT_FOUND')}")
                                logger.info(f"ACEs count for {path}: {len(perms.get('aces', []))}")
                        
                        path_issues = self._analyze_path_results(path, scan_result, scan.id)
                        logger.info(f"Raw issues found for {path}: {len(path_issues)} - {[issue.get('issue_type', {}).value if hasattr(issue.get('issue_type', {}), 'value') else issue.get('issue_type') for issue in path_issues]}")
                        
                        # Filter out non-significant issues
                        significant_issues = self._filter_significant_issues(path_issues)
                        logger.info(f"Significant issues for {path}: {len(significant_issues)} - {[issue.get('issue_type', {}).value if hasattr(issue.get('issue_type', {}), 'value') else issue.get('issue_type') for issue in significant_issues]}")
                        
                        if significant_issues:
                            logger.info(f"Adding {len(significant_issues)} significant issues for {path}")
                            all_issues.extend(significant_issues)
                        else:
                            logger.info(f"No significant issues found for {path}")
                        processed_paths += 1
                    else:
                        logger.warning(f"Failed to scan path {path}: {scan_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"Error scanning path {path}: {str(e)}")
                    continue
            
            # Calculate overall health score
            overall_score = self._calculate_health_score(all_issues)
            logger.info(f"Health scan summary: {processed_paths} paths processed, {len(all_issues)} issues found, score: {overall_score}")
            
            # Update scan record
            scan.end_time = datetime.now(timezone.utc)
            scan.status = "completed"
            scan.processed_paths = processed_paths
            scan.issues_found = len(all_issues)
            scan.overall_score = overall_score
            
            # Store issues in database with deduplication
            for issue_data in all_issues:
                # Check if similar active issue already exists
                existing_issue = db.query(Issue).filter(
                    Issue.path == issue_data['path'],
                    Issue.issue_type == issue_data['issue_type'],
                    Issue.status == IssueStatus.ACTIVE
                ).first()
                
                if existing_issue:
                    # Update last_seen timestamp for existing issue
                    existing_issue.last_seen = datetime.now(timezone.utc)
                    existing_issue.health_scan_id = scan.id
                    # Update any changed details
                    existing_issue.severity = issue_data['severity']
                    existing_issue.description = issue_data['description']
                    existing_issue.affected_principals = issue_data.get('affected_principals', [])
                    existing_issue.acl_details = issue_data.get('acl_details', {})
                    existing_issue.recommendations = issue_data.get('recommendations')
                    existing_issue.risk_score = issue_data.get('risk_score', 0.0)
                else:
                    # Create new issue only if it doesn't exist
                    issue = Issue(**issue_data)
                    db.add(issue)
            
            # Create health metrics record
            metrics = self._create_health_metrics(scan.id, all_issues, overall_score, processed_paths)
            db.add(metrics)
            
            # Record score history
            severity_counts_history = self._get_severity_counts_for_history(all_issues)
            score_history = HealthScoreHistory(
                timestamp=datetime.now(timezone.utc),
                score=overall_score,
                issue_count=len(all_issues),
                scan_id=scan.id,
                **severity_counts_history
            )
            db.add(score_history)
            
            db.commit()
            logger.info(f"Health scan {scan.id} completed with score {overall_score:.1f}")
            return scan.id
            
        except Exception as e:
            logger.error(f"Error during health scan: {str(e)}")
            if 'scan' in locals():
                scan.status = "failed"
                scan.error_message = str(e)
                scan.end_time = datetime.now(timezone.utc)
                db.commit()
            raise
        finally:
            db.close()
    
    def _analyze_path_results(self, path: str, scan_result: Dict[str, Any], scan_id: int) -> List[Dict[str, Any]]:
        """Analyze scan results for a single path and detect issues."""
        issues = []
        
        # Handle different scan result formats
        # Check if this is a nested structure with 'permissions' key
        if 'permissions' in scan_result and isinstance(scan_result['permissions'], dict):
            # Extract ACEs from nested structure
            aces = scan_result['permissions'].get('aces', [])
            inheritance_data = scan_result['permissions']
        else:
            # Direct structure
            aces = scan_result.get('aces', [])
            inheritance_data = scan_result
            
        if not aces:
            logger.warning(f"No ACEs found for path {path}")
            logger.info(f"Scan result structure for {path}: {list(scan_result.keys())}")
            if 'permissions' in scan_result:
                logger.info(f"Permissions structure: {list(scan_result['permissions'].keys()) if isinstance(scan_result['permissions'], dict) else type(scan_result['permissions'])}")
            return issues
        
        # Check for broken inheritance
        inheritance_issue = self._check_broken_inheritance(path, inheritance_data)
        if inheritance_issue:
            inheritance_issue['health_scan_id'] = scan_id
            issues.append(inheritance_issue)
        
        # Check for direct user ACEs
        direct_user_issues = self._check_direct_user_aces(path, aces)
        for issue in direct_user_issues:
            issue['health_scan_id'] = scan_id
            issues.append(issue)
        
        # Check for orphaned SIDs
        orphaned_issues = self._check_orphaned_sids(path, aces)
        for issue in orphaned_issues:
            issue['health_scan_id'] = scan_id
            issues.append(issue)
        
        # Check for excessive ACE count
        excessive_ace_issue = self._check_excessive_ace_count(path, aces)
        if excessive_ace_issue:
            excessive_ace_issue['health_scan_id'] = scan_id
            issues.append(excessive_ace_issue)
        
        # Check for conflicting deny order
        conflicting_deny_issues = self._check_conflicting_deny_order(path, aces)
        for issue in conflicting_deny_issues:
            issue['health_scan_id'] = scan_id
            issues.append(issue)
        
        # Check for over-permissive groups
        over_permissive_issues = self._check_over_permissive_groups(path, aces)
        for issue in over_permissive_issues:
            issue['health_scan_id'] = scan_id
            issues.append(issue)
        
        return issues
    
    def _filter_significant_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out issues that are not significant or are false positives."""
        significant_issues = []
        
        for issue in issues:
            # Skip issues with very low risk scores - lowered threshold from 5.0 to 2.0
            if issue.get('risk_score', 0) < 2.0:
                continue
                
            # Skip direct user ACE issues if they only affect built-in accounts
            if issue.get('issue_type') == IssueType.DIRECT_USER_ACE:
                affected_principals = issue.get('affected_principals', [])
                if not affected_principals:
                    continue
                    
                # Check if all affected principals are built-in accounts
                builtin_accounts = [
                    'administrator', 'guest', 'krbtgt', 'default account',
                    'default user', 'wdagutilityaccount'
                ]
                
                non_builtin_principals = [
                    p for p in affected_principals 
                    if p.lower() not in builtin_accounts and 
                    not p.lower().startswith('nt ') and
                    not p.lower().startswith('iis_')
                ]
                
                if not non_builtin_principals:
                    logger.info(f"Skipping direct user ACE issue for {issue.get('path')} - only affects built-in accounts")
                    continue
                    
                # Update the issue to only include non-builtin principals
                issue['affected_principals'] = non_builtin_principals
                issue['description'] = f"Found {len(non_builtin_principals)} direct user ACEs in {issue.get('path')}. Best practice is to grant permissions to security groups instead of individual users."
            
            # Skip orphaned SID issues with very few SIDs - lowered threshold from 2 to 1
            if issue.get('issue_type') == IssueType.ORPHANED_SID:
                affected_principals = issue.get('affected_principals', [])
                if len(affected_principals) < 1:
                    continue
            
            # Skip excessive ACE count for paths with reasonable counts - lowered threshold from 30 to 15
            if issue.get('issue_type') == IssueType.EXCESSIVE_ACE_COUNT:
                acl_details = issue.get('acl_details', {})
                ace_count = acl_details.get('ace_count', 0)
                if ace_count < 15:  # Lower threshold for reporting
                    continue
            
            significant_issues.append(issue)
            
        return significant_issues
    
    def _check_broken_inheritance(self, path: str, scan_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if inheritance is broken (disabled)."""
        # Check for inheritance_enabled in the permissions section first, then fall back to top level
        permissions = scan_result.get('permissions', {})
        inheritance_enabled = permissions.get('inheritance_enabled', scan_result.get('inheritance_enabled', True))
        logger.info(f"Checking broken inheritance for {path}: inheritance_enabled = {inheritance_enabled} (type: {type(inheritance_enabled)})")
        logger.info(f"Scan result keys for inheritance check: {list(scan_result.keys())}")
        logger.info(f"Permissions keys for inheritance check: {list(permissions.keys())}")
        
        if not inheritance_enabled:
            logger.info(f"BROKEN INHERITANCE DETECTED for {path}")
            return {
                'issue_type': IssueType.BROKEN_INHERITANCE,
                'severity': IssueSeverity.MEDIUM,
                'path': path,
                'title': 'Inheritance Disabled',
                'description': f'ACL inheritance is disabled for {path}, which may indicate configuration issues or security risks.',
                'risk_score': 15.0,
                'recommendations': 'Review why inheritance is disabled. Consider re-enabling if appropriate, or document the business justification.',
                'acl_details': {'inheritance_enabled': inheritance_enabled},
                'first_detected': datetime.now(timezone.utc),
                'last_seen': datetime.now(timezone.utc)
            }
        else:
            logger.info(f"No broken inheritance issue for {path} (inheritance_enabled = {inheritance_enabled})")
        return None
    
    def _check_direct_user_aces(self, path: str, aces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for direct user ACEs (permissions granted to users instead of groups)."""
        issues = []
        direct_user_aces = []
        
        for ace in aces:
            trustee = ace.get('trustee', {})
            trustee_name = trustee.get('name', '').lower()
            trustee_domain = trustee.get('domain', '').lower()
            
            # Check if this is a built-in account that should be excluded
            builtin_accounts = [
                'administrator', 'guest', 'krbtgt', 'default account',
                'default user', 'wdagutilityaccount'
            ]
            builtin_domains = ['nt authority', 'builtin', 'nt service']
            
            is_builtin = (trustee_name in builtin_accounts or 
                         trustee_domain in builtin_domains or
                         trustee_name.startswith('nt ') or
                         trustee_name.startswith('iis_'))
            
            # Check if this is a user (not a group)
            # Look for user indicators in the trustee structure
            is_user = False
            
            # Check if explicitly marked as user type
            if trustee.get('type') == 'user':
                is_user = True
            # Check if it's a domain user (not a built-in account or group)
            elif trustee_domain not in builtin_domains and not trustee_name.endswith('_staff') and not trustee_name.endswith('_viewers'):
                # Check if it has user-like characteristics
                if '@' in trustee_name or '.' in trustee_name:
                    is_user = True
            
            # Exclude system accounts
            is_system = (trustee.get('is_system', False) or 
                        trustee_name in ['system', 'creator owner'] or
                        trustee_domain == 'nt authority')
            
            # Only report non-builtin user accounts
            if is_user and not is_system and not is_builtin:
                direct_user_aces.append(ace)
                logger.info(f"Found direct user ACE: {trustee.get('full_name', trustee_name)}")
        
        # Report any direct user ACEs as an issue (best practice is to use groups)
        if len(direct_user_aces) > 0:
            severity = IssueSeverity.HIGH if len(direct_user_aces) > 5 else IssueSeverity.MEDIUM
            
            issues.append({
                'issue_type': IssueType.DIRECT_USER_ACE,
                'severity': severity,
                'path': path,
                'title': f'Excessive Direct User Permissions ({len(direct_user_aces)})',
                'description': f'Found {len(direct_user_aces)} direct user ACEs in {path}. Best practice is to grant permissions to security groups instead of individual users.',
                'risk_score': 10.0 + (len(direct_user_aces) * 2.0),
                'affected_principals': [ace['trustee']['name'] for ace in direct_user_aces],
                'recommendations': 'Replace direct user permissions with security group memberships. Create appropriate security groups and grant permissions to groups instead.',
                'acl_details': {'direct_user_aces': direct_user_aces},
                'first_detected': datetime.now(timezone.utc),
                'last_seen': datetime.now(timezone.utc)
            })
        
        return issues
    
    def _check_orphaned_sids(self, path: str, aces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for orphaned SIDs (SIDs that cannot be resolved)."""
        issues = []
        orphaned_sids = []
        
        for ace in aces:
            trustee = ace.get('trustee', {})
            if trustee.get('name', '').startswith('S-') and trustee.get('type') == 'unknown':
                orphaned_sids.append(ace)
        
        if orphaned_sids:
            severity = IssueSeverity.MEDIUM if len(orphaned_sids) > 3 else IssueSeverity.LOW
            
            issues.append({
                'issue_type': IssueType.ORPHANED_SID,
                'severity': severity,
                'path': path,
                'title': f'Orphaned SIDs ({len(orphaned_sids)})',
                'description': f'Found {len(orphaned_sids)} orphaned SIDs in {path}. These are security identifiers that cannot be resolved to user or group names.',
                'risk_score': 5.0 + (len(orphaned_sids) * 1.0),
                'affected_principals': [ace['trustee']['sid'] for ace in orphaned_sids],
                'recommendations': 'Remove orphaned SIDs from ACLs. These may be from deleted users or groups and pose security risks.',
                'acl_details': {'orphaned_sids': orphaned_sids},
                'first_detected': datetime.now(timezone.utc),
                'last_seen': datetime.now(timezone.utc)
            })
        
        return issues
    
    def _check_excessive_ace_count(self, path: str, aces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Check for excessive number of ACEs."""
        ace_count = len(aces)
        if ace_count > self.config.max_ace_count_threshold:
            severity = IssueSeverity.HIGH if ace_count > 100 else IssueSeverity.MEDIUM
            
            return {
                'issue_type': IssueType.EXCESSIVE_ACE_COUNT,
                'severity': severity,
                'path': path,
                'title': f'Excessive ACE Count ({ace_count})',
                'description': f'Path {path} has {ace_count} ACEs, which exceeds the recommended maximum of {self.config.max_ace_count_threshold}.',
                'risk_score': 20.0 + (ace_count * 0.5),
                'recommendations': 'Consolidate permissions by using security groups instead of individual ACEs. Review and remove unnecessary permissions.',
                'acl_details': {'ace_count': ace_count, 'threshold': self.config.max_ace_count_threshold},
                'first_detected': datetime.now(timezone.utc),
                'last_seen': datetime.now(timezone.utc)
            }
        return None
    
    def _check_conflicting_deny_order(self, path: str, aces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for deny ACEs that come after allow ACEs (order matters)."""
        issues = []
        
        # Find deny ACEs that come after allow ACEs for the same trustee
        trustee_aces = {}
        for i, ace in enumerate(aces):
            trustee_sid = ace.get('trustee', {}).get('sid', '')
            if trustee_sid not in trustee_aces:
                trustee_aces[trustee_sid] = []
            trustee_aces[trustee_sid].append((i, ace))
        
        conflicting_trustees = []
        for trustee_sid, trustee_ace_list in trustee_aces.items():
            allow_indices = []
            deny_indices = []
            
            for i, ace in trustee_ace_list:
                if ace.get('type') == 'allow':
                    allow_indices.append(i)
                elif ace.get('type') == 'deny':
                    deny_indices.append(i)
            
            # Check if any deny ACEs come after allow ACEs
            for deny_idx in deny_indices:
                if any(allow_idx < deny_idx for allow_idx in allow_indices):
                    conflicting_trustees.append({
                        'trustee': ace.get('trustee', {}),
                        'deny_index': deny_idx,
                        'allow_indices': [idx for idx in allow_indices if idx < deny_idx]
                    })
        
        if conflicting_trustees:
            issues.append({
                'issue_type': IssueType.CONFLICTING_DENY_ORDER,
                'severity': IssueSeverity.HIGH,
                'path': path,
                'title': f'Conflicting ACE Order ({len(conflicting_trustees)} trustees)',
                'description': f'Found deny ACEs that come after allow ACEs for the same trustees in {path}. This may result in ineffective access control.',
                'risk_score': 25.0 + (len(conflicting_trustees) * 5.0),
                'affected_principals': [ct['trustee']['name'] for ct in conflicting_trustees],
                'recommendations': 'Reorder ACEs so that deny ACEs come before allow ACEs. Review ACL structure and remove conflicting permissions.',
                'acl_details': {'conflicting_trustees': conflicting_trustees},
                'first_detected': datetime.now(timezone.utc),
                'last_seen': datetime.now(timezone.utc)
            })
        
        return issues
    
    def _check_over_permissive_groups(self, path: str, aces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for over-permissive group permissions."""
        issues = []
        critical_group_aces = []
        
        for ace in aces:
            trustee = ace.get('trustee', {})
            trustee_name = trustee.get('name', '')
            
            if ace.get('type') == 'allow' and any(cg.lower() in trustee_name.lower() for cg in self.config.critical_groups):
                critical_group_aces.append(ace)
        
        if critical_group_aces:
            severity = IssueSeverity.CRITICAL if len(critical_group_aces) > 2 else IssueSeverity.HIGH
            
            issues.append({
                'issue_type': IssueType.OVER_PERMISSIVE_GROUPS,
                'severity': severity,
                'path': path,
                'title': f'Over-Permissive Group Access ({len(critical_group_aces)})',
                'description': f'Found {len(critical_group_aces)} ACEs granting permissions to high-privilege groups in {path}.',
                'risk_score': 25.0 + (len(critical_group_aces) * 10.0),
                'affected_principals': [ace['trustee']['name'] for ace in critical_group_aces],
                'recommendations': 'Review permissions granted to high-privilege groups. Use principle of least privilege and create more specific security groups.',
                'acl_details': {'critical_group_aces': critical_group_aces},
                'first_detected': datetime.now(timezone.utc),
                'last_seen': datetime.now(timezone.utc)
            })
        
        return issues
    
    def _calculate_health_score(self, issues: List[Dict[str, Any]]) -> float:
        """Calculate overall health score based on detected issues."""
        if not issues:
            return 100.0
        
        total_risk = 0.0
        max_possible_risk = sum(self.config.score_weights.values())
        
        severity_multipliers = {
            IssueSeverity.LOW: 0.25,
            IssueSeverity.MEDIUM: 0.5,
            IssueSeverity.HIGH: 0.75,
            IssueSeverity.CRITICAL: 1.0
        }
        
        for issue in issues:
            issue_type = issue['issue_type']
            severity = issue['severity']
            
            base_weight = self.config.score_weights.get(issue_type.value, 10.0)
            severity_multiplier = severity_multipliers.get(severity, 0.5)
            
            total_risk += base_weight * severity_multiplier
        
        # Cap total risk at max possible risk
        total_risk = min(total_risk, max_possible_risk)
        
        # Calculate score (100 - normalized risk percentage)
        risk_percentage = (total_risk / max_possible_risk) * 100
        score = max(0.0, 100.0 - risk_percentage)
        
        return round(score, 1)
    
    def _create_health_metrics(self, scan_id: int, issues: List[Dict[str, Any]], score: float, paths_scanned: int) -> HealthMetrics:
        """Create health metrics record."""
        severity_counts = self._get_severity_counts(issues)
        type_counts = self._get_type_counts(issues)
        
        return HealthMetrics(
            scan_date=datetime.now(timezone.utc),
            overall_score=score,
            total_issues=len(issues),
            total_paths_scanned=paths_scanned,
            **severity_counts,
            **type_counts
        )
    
    def _get_severity_counts(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get issue counts by severity."""
        counts = {
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0
        }
        
        for issue in issues:
            severity = issue['severity']
            if severity == IssueSeverity.CRITICAL:
                counts['critical_issues'] += 1
            elif severity == IssueSeverity.HIGH:
                counts['high_issues'] += 1
            elif severity == IssueSeverity.MEDIUM:
                counts['medium_issues'] += 1
            elif severity == IssueSeverity.LOW:
                counts['low_issues'] += 1
        
        return counts
    
    def _get_severity_counts_for_history(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get issue counts by severity for HealthScoreHistory (uses _count suffix)."""
        counts = {
            'critical_count': 0,
            'high_count': 0,
            'medium_count': 0,
            'low_count': 0
        }
        
        for issue in issues:
            severity = issue['severity']
            if severity == IssueSeverity.CRITICAL:
                counts['critical_count'] += 1
            elif severity == IssueSeverity.HIGH:
                counts['high_count'] += 1
            elif severity == IssueSeverity.MEDIUM:
                counts['medium_count'] += 1
            elif severity == IssueSeverity.LOW:
                counts['low_count'] += 1
        
        return counts
    
    def _get_type_counts(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get issue counts by type."""
        counts = {
            'broken_inheritance_count': 0,
            'direct_user_ace_count': 0,
            'orphaned_sid_count': 0,
            'excessive_ace_count': 0,
            'conflicting_deny_order_count': 0,
            'over_permissive_groups_count': 0
        }
        
        for issue in issues:
            issue_type = issue['issue_type']
            if issue_type == IssueType.BROKEN_INHERITANCE:
                counts['broken_inheritance_count'] += 1
            elif issue_type == IssueType.DIRECT_USER_ACE:
                counts['direct_user_ace_count'] += 1
            elif issue_type == IssueType.ORPHANED_SID:
                counts['orphaned_sid_count'] += 1
            elif issue_type == IssueType.EXCESSIVE_ACE_COUNT:
                counts['excessive_ace_count'] += 1
            elif issue_type == IssueType.CONFLICTING_DENY_ORDER:
                counts['conflicting_deny_order_count'] += 1
            elif issue_type == IssueType.OVER_PERMISSIVE_GROUPS:
                counts['over_permissive_groups_count'] += 1
        
        return counts
    
    def get_health_score(self) -> Dict[str, Any]:
        """Get current health score and issue summary."""
        db = SessionLocal()
        try:
            # Test database connection first
            try:
                from sqlalchemy import text
                db.execute(text("SELECT 1"))
            except Exception as e:
                logger.error(f"Database connection failed: {str(e)}")
                return {
                    'score': 0,
                    'issues': {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                    'last_scan': None,
                    'error': 'Database connection failed'
                }
            
            # Get latest score
            try:
                latest_score = db.query(HealthScoreHistory).order_by(HealthScoreHistory.timestamp.desc()).first()
            except Exception as e:
                logger.error(f"Failed to query HealthScoreHistory table: {str(e)}")
                # Table might not exist, return default values
                return {
                    'score': 0,
                    'issues': {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                    'last_scan': None,
                    'error': 'Health score table not found or not initialized'
                }
            
            if not latest_score:
                return {
                    'score': 0,
                    'issues': {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                    'last_scan': None,
                    'message': 'No health scans have been performed yet'
                }
            
            # Get current active issues for type counts
            type_counts = {'broken_inheritance': 0, 'direct_user_ace': 0, 'orphaned_sid': 0, 
                          'excessive_ace_count': 0, 'conflicting_deny_order': 0, 'over_permissive_groups': 0}
            
            try:
                active_issues = db.query(Issue).filter(Issue.status == IssueStatus.ACTIVE).all()
                for issue in active_issues:
                    issue_type_name = issue.issue_type.value
                    if issue_type_name in type_counts:
                        type_counts[issue_type_name] += 1
            except Exception as e:
                logger.warning(f"Could not get issue type counts: {str(e)}")
            
            return {
                'score': latest_score.score,
                'issues': {
                    'total': latest_score.issue_count,
                    'critical': latest_score.critical_count,
                    'high': latest_score.high_count,
                    'medium': latest_score.medium_count,
                    'low': latest_score.low_count
                },
                'issue_types': type_counts,
                'last_scan': latest_score.timestamp.isoformat() if latest_score.timestamp else None
            }
        except Exception as e:
            logger.error(f"Unexpected error in get_health_score: {str(e)}")
            return {
                'score': 0,
                'issues': {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                'last_scan': None,
                'error': str(e)
            }
        finally:
            db.close()
    
    def get_issues(self, skip: int = 0, limit: int = 100, severity: str = None, issue_type: str = None, path_filter: str = None) -> Dict[str, Any]:
        """Get paginated list of issues."""
        db = SessionLocal()
        try:
            # Test database connection first
            try:
                from sqlalchemy import text
                db.execute(text("SELECT 1"))
            except Exception as e:
                logger.error(f"Database connection failed in get_issues: {str(e)}")
                return {
                    'total': 0,
                    'issues': [],
                    'skip': skip,
                    'limit': limit,
                    'error': 'Database connection failed'
                }
            
            try:
                query = db.query(Issue).filter(Issue.status == IssueStatus.ACTIVE)
                
                if severity:
                    query = query.filter(Issue.severity == severity)
                
                if issue_type:
                    query = query.filter(Issue.issue_type == issue_type)
                
                if path_filter:
                    query = query.filter(Issue.path.contains(path_filter))
                
                total = query.count()
                issues = query.order_by(Issue.severity.desc(), Issue.last_seen.desc()).offset(skip).limit(limit).all()
                
                return {
                    'total': total,
                    'issues': [
                        {
                            'id': issue.id,
                            'type': issue.issue_type.value,
                            'severity': issue.severity.value,
                            'path': issue.path,
                            'title': issue.title,
                            'description': issue.description,
                            'risk_score': issue.risk_score,
                            'first_detected': issue.first_detected.isoformat(),
                            'last_seen': issue.last_seen.isoformat(),
                            'affected_principals': issue.affected_principals,
                            'recommendations': issue.recommendations
                        }
                        for issue in issues
                    ],
                    'skip': skip,
                    'limit': limit
                }
            except Exception as e:
                logger.error(f"Failed to query Issue table: {str(e)}")
                return {
                    'total': 0,
                    'issues': [],
                    'skip': skip,
                    'limit': limit,
                    'error': 'Health issues table not found or not initialized'
                }
        except Exception as e:
            logger.error(f"Unexpected error in get_issues: {str(e)}")
            return {
                'total': 0,
                'issues': [],
                'skip': skip,
                'limit': limit,
                'error': str(e)
            }
        finally:
            db.close()