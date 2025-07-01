import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { healthApi } from '../api/health';
import type { HealthPageFilters, HealthPageSortConfig } from '../types/health';

export function useHealthScore() {
    return useQuery({
        queryKey: ['health', 'score'],
        queryFn: healthApi.getHealthScore,
        refetchInterval: 60000, // Refetch every minute
    });
}

interface UseIssuesParams {
    page: number;
    pageSize: number;
    filters: HealthPageFilters;
    sort: HealthPageSortConfig;
}

export function useIssues({ page, pageSize, filters, sort }: UseIssuesParams) {
    return useQuery({
        queryKey: ['health', 'issues', page, pageSize, filters, sort],
        queryFn: () => healthApi.getIssues({
            skip: page * pageSize,
            limit: pageSize,
            severity: filters.severity?.length ? filters.severity.join(',') : undefined,
            issue_type: filters.issueType?.length ? filters.issueType.join(',') : undefined,
            path_filter: filters.pathSubstring,
            search: (filters as any).searchQuery,
        }),
        keepPreviousData: true,
    });
}

export function useIssueDetails(issueId: string | null) {
    return useQuery({
        queryKey: ['health', 'issues', issueId],
        queryFn: () => issueId ? healthApi.getIssueDetails(issueId) : null,
        enabled: !!issueId,
    });
}

export function useRunHealthScan() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: healthApi.runHealthScan,
        onSuccess: () => {
            // Delay invalidation to allow background scan to complete
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['health'] });
                // Also invalidate permissions/scan data since health scan may create new scan results
                queryClient.invalidateQueries({ queryKey: ['folders'] });
                queryClient.invalidateQueries({ queryKey: ['permissions'] });
                queryClient.invalidateQueries({ queryKey: ['targets'] });
            }, 3000); // Increased delay to allow more time for scan completion
        },
    });
}

export function useExportIssues() {
    return useMutation({
        mutationFn: ({ format, filters }: { format: 'csv' | 'pdf'; filters?: HealthPageFilters }) => 
            healthApi.exportIssues(format, filters),
        onSuccess: (blob, { format }) => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `acl-health-issues-${new Date().toISOString().split('T')[0]}.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        },
    });
}