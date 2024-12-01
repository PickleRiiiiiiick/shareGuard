export interface FolderPermission {
    trustee_name: string;
    trustee_domain: string;
    trustee_sid: string;
    access_type: string;
    inherited: boolean;
    permissions: string[];
}

export interface FolderStructure {
    name: string;
    path: string;
    type: 'folder' | 'file';
    children?: FolderStructure[];
    permissions?: FolderPermission[];
    owner?: {
        name: string;
        domain: string;
        sid: string;
    };
    statistics?: {
        total_folders: number;
        total_files: number;
        depth: number;
    };
}

export interface PathInfo {
    permissions: string[];
    inherited: boolean;
    source_path?: string;
}

export interface FolderAccessInfo {
    username: string;
    domain: string;
    access_info: {
        readable: boolean;
        writable: boolean;
        paths: Record<string, PathInfo>;
    };
}

export interface FolderTreeOptions {
    maxDepth?: number;
    showFiles?: boolean;
    showPermissions?: boolean;
    showInherited?: boolean;
    expandedPaths?: string[];
}