import axios from 'axios';
import type { HealthScore, ACLIssue, HealthPageFilters } from '../types/health';

const api = axios.create({
    baseURL: '/api/v1/health',
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true
});

// Add auth token to requests if it exists
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Add response interceptor to handle errors gracefully
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // For health endpoints, we want to handle errors gracefully
        // and return error data instead of throwing
        if (error.response && error.response.status < 500) {
            // For 4xx errors, throw normally
            throw error;
        }
        // For 5xx errors or network errors, return a graceful error response
        console.error('Health API error:', error);
        return {
            data: {
                error: 'Database connection failed',
                message: 'Unable to connect to the health database. Please ensure the database is properly initialized.'
            }
        };
    }
);

interface GetIssuesParams {
    skip?: number;
    limit?: number;
    severity?: string;
    issue_type?: string;
    path_filter?: string;
    search?: string;
}

interface GetIssuesResponse {
    issues: ACLIssue[];
    total: number;
    skip: number;
    limit: number;
    error?: string;
}

export const healthApi = {
    getHealthScore: async (): Promise<HealthScore> => {
        const response = await api.get('/score');
        const data = response.data;
        
        // Check if there's an error in the response
        if ('error' in data) {
            return data; // Return error as-is for error handling
        }
        
        // Transform backend format to frontend format
        return {
            score: data.score || 0,
            lastScanTimestamp: data.last_scan || new Date().toISOString(),
            issueCountBySeverity: {
                critical: data.issues?.critical || 0,
                high: data.issues?.high || 0,
                medium: data.issues?.medium || 0,
                low: data.issues?.low || 0
            },
            issueCountByType: {
                broken_inheritance: data.issue_types?.broken_inheritance || 0,
                direct_user_ace: data.issue_types?.direct_user_ace || 0,
                orphaned_sid: data.issue_types?.orphaned_sid || 0,
                excessive_ace_count: data.issue_types?.excessive_ace_count || 0,
                conflicting_deny_order: data.issue_types?.conflicting_deny_order || 0,
                over_permissive_groups: data.issue_types?.over_permissive_groups || 0
            }
        };
    },

    getIssues: async (params: GetIssuesParams): Promise<GetIssuesResponse> => {
        const response = await api.get('/issues', { params });
        // Transform snake_case to camelCase for issues
        if (response.data.issues) {
            response.data.issues = response.data.issues.map((issue: any) => ({
                id: issue.id,
                type: issue.type,
                severity: issue.severity,
                path: issue.path,
                description: issue.description,
                affectedPrincipals: issue.affected_principals || [],
                detectedAt: issue.last_seen || issue.first_detected,
                details: {
                    currentACL: issue.acl_details,
                    recommendedACL: issue.recommendations,
                    remediationSteps: issue.impact_description ? [issue.impact_description] : []
                }
            }));
        }
        return response.data;
    },

    runHealthScan: async (): Promise<void> => {
        await api.post('/scan');
    },

    getIssueDetails: async (issueId: string): Promise<ACLIssue> => {
        const response = await api.get(`/issues/${issueId}`);
        // Transform snake_case to camelCase
        const issue = response.data;
        return {
            id: issue.id,
            type: issue.type,
            severity: issue.severity,
            path: issue.path,
            description: issue.description,
            affectedPrincipals: issue.affected_principals || [],
            detectedAt: issue.last_seen || issue.first_detected,
            details: {
                currentACL: issue.acl_details,
                recommendedACL: issue.recommendations,
                remediationSteps: issue.impact_description ? [issue.impact_description] : []
            }
        };
    },

    exportIssues: async (format: 'csv' | 'pdf', filters?: HealthPageFilters): Promise<Blob> => {
        const params: any = { format };
        
        if (filters) {
            if (filters.severity?.length) params.severity = filters.severity.join(',');
            if (filters.issueType?.length) params.issue_type = filters.issueType.join(',');
            if (filters.pathSubstring) params.path_filter = filters.pathSubstring;
        }
        
        const response = await api.get(`/issues/export`, {
            params,
            responseType: 'blob'
        });
        return response.data;
    }
};