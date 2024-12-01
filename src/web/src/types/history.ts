export type ChangeType = 'added' | 'removed' | 'modified';

export interface PermissionHistoryEntry {
    id: number;
    scan_job_id: number;
    access_entry_id: number;
    change_type: ChangeType;
    previous_state: any;
    current_state: any;
    detected_time: string;
    path: string;
    trustee_name: string;
    trustee_domain: string;
}

export interface PermissionHistoryFilters {
    startDate?: string;
    endDate?: string;
    path?: string;
    trustee?: string;
    changeType?: ChangeType;
}