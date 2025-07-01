import { useQuery, useMutation, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import { api } from '@/utils/api';
import type { ScanTarget, TargetStats } from '@/types/target';
import type { FolderStructure, FolderPermission, FolderAccessInfo, FolderTreeOptions } from '@/types/folder';

// Target hooks
export function useCreateTarget() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (newTarget: Omit<ScanTarget, 'id' | 'created_at' | 'created_by'>) =>
            api.targets.post<ScanTarget>('/', newTarget),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['targets'] });
        },
    });
}

export function useUpdateTarget() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, data }: { id: number; data: Partial<ScanTarget> }) =>
            api.targets.put<ScanTarget>(`/${id}`, data),
        onSuccess: (_, { id }) => {
            queryClient.invalidateQueries({ queryKey: ['targets'] });
            queryClient.invalidateQueries({ queryKey: ['target', id] });
        },
    });
}

export function useDeleteTarget() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: number) => api.targets.delete(`/${id}`),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['targets'] });
        },
    });
}

export function useTargets(filters?: Record<string, any>): UseQueryResult<ScanTarget[]> {
    return useQuery({
        queryKey: ['targets', filters],
        queryFn: async () => {
            const params = new URLSearchParams();
            Object.entries(filters || {}).forEach(([key, value]) => {
                if (value) params.append(key, String(value));
            });
            return await api.targets.get<ScanTarget[]>(`/?${params.toString()}`);
        }
    });
}

export function useTargetStats(targetId: number): UseQueryResult<TargetStats> {
    return useQuery({
        queryKey: ['targetStats', targetId],
        queryFn: async () => await api.targets.get<TargetStats>(`/${targetId}/stats`)
    });
}

// Folder hooks
export function useFolderStructure(path: string, options?: FolderTreeOptions): UseQueryResult<FolderStructure> {
    return useQuery({
        queryKey: ['folderStructure', path, options],
        queryFn: async () => {
            const params = new URLSearchParams();
            if (options?.maxDepth) params.append('max_depth', options.maxDepth.toString());
            const response = await api.folders.get<FolderStructure>(`/structure?root_path=${encodeURIComponent(path)}&${params.toString()}`);
            return response;
        },
        enabled: !!path,
        staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
    });
}

export function useFolderPermissions(
    path: string,
    options?: { includeInherited: boolean }
): UseQueryResult<{ permissions: FolderPermission[] }> {
    return useQuery({
        queryKey: ['folderPermissions', path, options],
        queryFn: async () => {
            const params = new URLSearchParams();
            if (options?.includeInherited !== undefined) {
                params.append('include_inherited', options.includeInherited.toString());
            }
            const response = await api.folders.get<{ permissions: FolderPermission[] }>(
                `/permissions?path=${encodeURIComponent(path)}&${params.toString()}`
            );
            return response;
        },
        enabled: !!path,
        staleTime: 5 * 60 * 1000,
    });
}

export function useUserFolderAccess(
    username: string,
    domain: string,
    basePath?: string
): UseQueryResult<FolderAccessInfo> {
    return useQuery({
        queryKey: ['folderAccess', username, domain, basePath],
        queryFn: async () => {
            const params = new URLSearchParams({
                username,
                domain,
                ...(basePath && { base_path: basePath }),
            });
            const response = await api.folders.get<FolderAccessInfo>(`/access/${username}?${params.toString()}`);
            return response;
        },
        enabled: !!username && !!domain,
    });
}

export function useValidateFolderAccess() {
    return useMutation({
        mutationFn: async ({ path, checkWrite = false }: { path: string; checkWrite?: boolean }) => {
            const params = new URLSearchParams({
                path,
                check_write: checkWrite.toString(),
            });
            const response = await api.folders.post<{ valid: boolean; readable: boolean; writable: boolean }>(
                `/validate?${params.toString()}`
            );
            return response;
        }
    });
}
