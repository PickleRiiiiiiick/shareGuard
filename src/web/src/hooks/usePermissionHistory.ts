import { useQuery, UseQueryResult } from 'react-query';
import { api } from '@/utils/api';
import type { PermissionHistoryEntry, PermissionHistoryFilters } from '@/types/history';

export function usePermissionHistory(
    filters: PermissionHistoryFilters
): UseQueryResult<PermissionHistoryEntry[]> {
    const queryKey = ['permissionHistory', filters];

    return useQuery<PermissionHistoryEntry[]>(
        queryKey,
        async () => {
            const params = new URLSearchParams();
            if (filters.startDate) params.append('start_date', filters.startDate);
            if (filters.endDate) params.append('end_date', filters.endDate);
            if (filters.path) params.append('path', filters.path);
            if (filters.trustee) params.append('trustee', filters.trustee);
            if (filters.changeType) params.append('change_type', filters.changeType);

            const response = await api.folders.get<PermissionHistoryEntry[]>(`/history?${params.toString()}`);
            return response;
        }
    );
}