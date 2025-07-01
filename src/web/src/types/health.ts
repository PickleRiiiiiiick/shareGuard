export type IssueSeverity = 'critical' | 'high' | 'medium' | 'low';

export type IssueType = 
    | 'broken_inheritance'
    | 'direct_user_ace' 
    | 'orphaned_sid'
    | 'excessive_ace_count'
    | 'conflicting_deny_order'
    | 'over_permissive_groups';

export interface HealthScore {
    score: number;
    lastScanTimestamp: string;
    issueCountBySeverity: {
        critical: number;
        high: number;
        medium: number;
        low: number;
    };
    issueCountByType: {
        broken_inheritance: number;
        direct_user_ace: number;
        orphaned_sid: number;
        excessive_ace_count: number;
        conflicting_deny_order: number;
        over_permissive_groups: number;
    };
}

export interface ACLIssue {
    id: string;
    severity: IssueSeverity;
    type: IssueType;
    path: string;
    description: string;
    affectedPrincipals: string[];
    detectedAt: string;
    details?: {
        currentACL?: any;
        recommendedACL?: any;
        remediationSteps?: string[];
    };
}

export interface HealthPageFilters {
    severity?: IssueSeverity[];
    issueType?: IssueType[];
    pathSubstring?: string;
    searchQuery?: string;
}

export interface HealthPageSortConfig {
    field: 'severity' | 'path' | 'type' | 'detectedAt';
    direction: 'asc' | 'desc';
}

export const ISSUE_TYPE_LABELS: Record<IssueType, string> = {
    broken_inheritance: 'Broken Inheritance',
    direct_user_ace: 'Direct User ACE',
    orphaned_sid: 'Orphaned SID',
    excessive_ace_count: 'Excessive ACE Count',
    conflicting_deny_order: 'Conflicting Deny Order',
    over_permissive_groups: 'Over-permissive Groups'
};

export const SEVERITY_COLORS: Record<IssueSeverity, { bg: string; text: string; border: string }> = {
    critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
    high: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
    medium: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
    low: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' }
};

export const HEALTH_SCORE_THRESHOLDS = {
    good: 80,
    warning: 60
};