export interface ScanJob {
    id: number;
    target_id: number;
    scan_type: string;
    start_time: string;
    end_time?: string;
    status: 'running' | 'completed' | 'failed';
    parameters: {
        path: string;
        include_subfolders: boolean;
        max_depth?: number;
        simplified_system: boolean;
        include_inherited: boolean;
    };
    error_message?: string;
    created_by: string;
}

export interface ScanStats {
    jobs: {
        total: number;
        successful: number;
        failed: number;
        success_rate: number;
    };
    cache: {
        groups_cached: number;
        users_cached: number;
        paths_cached: number;
        memberships_cached: number;
        group_members_cached: number;
    };
    recent_scans: ScanJob[];
}