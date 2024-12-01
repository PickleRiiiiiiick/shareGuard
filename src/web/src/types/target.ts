import { ScanScheduleType } from '@/types/enums';

export interface ScanTargetCreate {
    name: string;
    path: string;
    description?: string;
    department?: string;
    owner?: string;
    sensitivity_level?: string;
    is_sensitive: boolean;
    scan_frequency: ScanScheduleType;
    max_depth?: number;
    exclude_patterns?: Record<string, string[]>;
    target_metadata?: Record<string, any>;
}

export interface ScanTarget extends ScanTargetCreate {
    id: number;
    created_at: string;
    last_scan_time?: string;
    created_by: string;
}

export interface TargetStats {
    total_scans: number;
    successful_scans: number;
    failed_scans: number;
    last_scan_status?: 'completed' | 'failed' | 'running';
    average_duration?: number;
}

export interface TargetFilters {
    searchTerm?: string;
    department?: string;
    sensitivity?: string;
    frequency?: ScanScheduleType;
    status?: 'active' | 'disabled';
}