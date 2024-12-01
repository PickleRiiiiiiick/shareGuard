import { useQuery, useMutation, UseQueryResult } from 'react-query';
import { api } from '@/utils/api';
import type {
    FolderStructure,
    FolderPermission,
    FolderAccessInfo,
    FolderTreeOptions,
} from '@/types/folder';

interface ApiResponse<T> {
    data: T;
}

// Hook to fetch folder structure
export function useFolderStructure(path: string, options?: FolderTreeOptions): UseQueryResult<FolderStructure> {
    const queryKey = ['folderStructure', path, options];

    return useQuery<FolderStructure>(
        queryKey,
        async () => {
            const params = new URLSearchParams();
            if (options?.maxDepth) params.append('max_depth', options.maxDepth.toString());
            const response = await api.folders.get<FolderStructure>(`/structure?root_path=${encodeURIComponent(path)}&${params.toString()}`);
            return response;
        },
        {
            enabled: !!path,
            staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
        }
    );
}

// Hook to fetch folder permissions
export function useFolderPermissions(
    path: string,
    options?: { includeInherited: boolean }
): UseQueryResult<{ permissions: FolderPermission[] }> {
    const queryKey = ['folderPermissions', path, options];

    return useQuery<{ permissions: FolderPermission[] }>(
        queryKey,
        async () => {
            const params = new URLSearchParams();
            if (options?.includeInherited !== undefined) {
                params.append('include_inherited', options.includeInherited.toString());
            }
            const response = await api.folders.get<{ permissions: FolderPermission[] }>(`/permissions?path=${encodeURIComponent(path)}&${params.toString()}`);
            return response;
        },
        {
            enabled: !!path,
            staleTime: 5 * 60 * 1000,
        }
    );
}

// Hook to fetch user folder access
export function useUserFolderAccess(
    username: string,
    domain: string,
    basePath?: string,
    options?: { enabled?: boolean }
): UseQueryResult<FolderAccessInfo> {
    const queryKey = ['folderAccess', username, domain, basePath];

    return useQuery<FolderAccessInfo>(
        queryKey,
        async () => {
            const params = new URLSearchParams({
                username,
                domain,
                ...(basePath && { base_path: basePath }),
            });
            const response = await api.folders.get<FolderAccessInfo>(`/access/${username}?${params.toString()}`);
            return response;
        },
        {
            enabled: options?.enabled && !!username && !!domain,
        }
    );
}

// Hook to validate folder access
export function useValidateFolderAccess() {
    return useMutation<ApiResponse<any>, Error, { path: string; checkWrite?: boolean }>(
        async ({ path, checkWrite = false }) => {
            const params = new URLSearchParams({
                path,
                check_write: checkWrite.toString(),
            });
            const response = await api.folders.post<ApiResponse<any>>(`/validate?${params.toString()}`);
            return response;
        }
    );
}