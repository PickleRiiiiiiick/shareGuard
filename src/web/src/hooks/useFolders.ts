import { useQuery, useMutation, UseQueryResult, useQueryClient } from 'react-query';
import { api } from '@/utils/api';
import { folderApi, type PermissionRequest, type PermissionResponse, type GroupMembersResponse } from '@/api/folders';
import { useAlert } from '@/contexts/AlertContext';
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
            const response = await api.folders.get<{ structure: FolderStructure; metadata: any }>(`/structure?root_path=${encodeURIComponent(path)}&${params.toString()}`);
            return response.structure;
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

// Hook to modify folder permissions with notifications
export function useModifyFolderPermissions() {
    const alert = useAlert();
    const queryClient = useQueryClient();

    return useMutation<PermissionResponse, Error, { path: string; permissionRequest: PermissionRequest }>(
        async ({ path, permissionRequest }) => {
            return await folderApi.modifyFolderPermissions(path, permissionRequest);
        },
        {
            onSuccess: (data) => {
                // Invalidate related queries to trigger refresh
                queryClient.invalidateQueries(['folderPermissions', data.path]);
                queryClient.invalidateQueries(['folderStructure']);
                
                // Show notification
                if (data.change_type === 'granted') {
                    alert.permissionGranted(
                        data.user_or_group,
                        data.path,
                        data.permissions.join(', ')
                    );
                } else {
                    alert.warning(
                        `Permission denied for ${data.user_or_group} on ${data.path}`
                    );
                }
            },
            onError: (error) => {
                alert.error(`Failed to modify permissions: ${error.message}`);
            }
        }
    );
}

// Hook to remove folder permissions with notifications
export function useRemoveFolderPermissions() {
    const alert = useAlert();
    const queryClient = useQueryClient();

    return useMutation<PermissionResponse, Error, { path: string; userOrGroup: string; domain: string }>(
        async ({ path, userOrGroup, domain }) => {
            return await folderApi.removeFolderPermissions(path, userOrGroup, domain);
        },
        {
            onSuccess: (data) => {
                // Invalidate related queries to trigger refresh
                queryClient.invalidateQueries(['folderPermissions', data.path]);
                queryClient.invalidateQueries(['folderStructure']);
                
                // Show notification
                alert.permissionRevoked(
                    data.user_or_group,
                    data.path,
                    'all permissions'
                );
            },
            onError: (error) => {
                alert.error(`Failed to remove permissions: ${error.message}`);
            }
        }
    );
}

// Hook to get group members
export function useGroupMembers(
    groupName: string,
    domain: string,
    includeNested: boolean = true,
    options?: { enabled?: boolean }
): UseQueryResult<GroupMembersResponse> {
    const queryKey = ['groupMembers', groupName, domain, includeNested];

    return useQuery<GroupMembersResponse>(
        queryKey,
        async () => {
            return await folderApi.getGroupMembers(groupName, domain, includeNested);
        },
        {
            enabled: options?.enabled && !!groupName && !!domain,
            staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
        }
    );
}