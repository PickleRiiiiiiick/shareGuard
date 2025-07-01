// 📄 File: /src/hooks/useScanResults.ts

import { useQuery, QueryObserverResult } from '@tanstack/react-query';
import { api } from '@/utils/api'; // ✅ Your existing Axios wrapper

// Define the expected structure of scan result items
export interface ScanResult {
    path: string;
    status: string;
    permissions: string[];
    detected_at: string;
    issue_summary?: string;
}

// Function to fetch scan results from the backend
const fetchScanResults = async (targetId: number): Promise<ScanResult[]> => {
    const response = await api.scan.get<ScanResult[]>(`/results/${targetId}`);
    return response;
};

// Hook to fetch scan results for a given target
export function useScanResults(targetId: number): QueryObserverResult<ScanResult[]> {
    return useQuery({
        queryKey: ['scan-results', targetId],
        queryFn: () => fetchScanResults(targetId),
        enabled: !!targetId
    });
}
