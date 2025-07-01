import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { api } from '@/utils/api';
import type { ScanJob, ScanStats } from '@/types/scan';

export function useScanStats(): UseQueryResult<ScanStats> {
    return useQuery<ScanStats>({
        queryKey: ['scanStats'],
        queryFn: async () => {
            const response = await api.scans.get<ScanStats>('/stats');
            return response;
        }
    });
}

export function useRecentScans(limit: number = 5): UseQueryResult<ScanJob[]> {
    return useQuery<ScanJob[]>({
        queryKey: ['recentScans', limit],
        queryFn: async () => {
            const response = await api.scans.get<ScanJob[]>(`/jobs?limit=${limit}&sort=start_time:desc`);
            return response;
        }
    });
}

export function useActiveScanJobs(): UseQueryResult<ScanJob[]> {
    return useQuery<ScanJob[]>({
        queryKey: ['activeScans'],
        queryFn: async () => {
            const response = await api.scans.get<ScanJob[]>('/jobs?status=running');
            return response;
        },
        refetchInterval: 5000,
    });
}