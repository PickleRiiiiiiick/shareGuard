export interface PermissionHistoryEntry {
    id: string;
    detected_time: string;
    trustee_domain: string;
    trustee_name: string;
    change_type: 'added' | 'removed' | 'modified';
    previous_state: string[];
    current_state: string[];
    path: string;
}

export interface PermissionHistoryFilters {
    path?: string;
    startDate?: Date;
    endDate?: Date;
    trustee?: string;
}