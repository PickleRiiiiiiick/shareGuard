import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1/folders',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface PermissionRequest {
  user_or_group: string;
  domain: string;
  permissions: string[];
  access_type?: 'allow' | 'deny';
}

export interface PermissionResponse {
  success: boolean;
  message: string;
  path: string;
  user_or_group: string;
  permissions: string[];
  change_type: string;
}

export interface FolderStructure {
  name: string;
  path: string;
  type: 'folder' | 'file';
  permissions: any[];
  children: FolderStructure[];
  owner?: any;
  statistics?: any;
}

export interface FolderPermissions {
  path: string;
  permissions: any;
  metadata: any;
}

export interface GroupMember {
  name: string;
  domain: string;
  full_name: string;
  type: string;
  sid?: string;
}

export interface GroupMembersInfo {
  group_name: string;
  domain: string;
  full_name: string;
  direct_members: GroupMember[];
  nested_groups: GroupMembersInfo[];
  all_members: GroupMember[];
  total_direct_members: number;
  total_all_members: number;
  error?: string;
}

export interface GroupMembersResponse {
  group_info: GroupMembersInfo;
  metadata: any;
}

export const folderApi = {
  // Existing read-only methods
  async getFolderStructure(rootPath: string, maxDepth?: number): Promise<{ structure: FolderStructure; metadata: any }> {
    const params = new URLSearchParams({ root_path: rootPath });
    if (maxDepth !== undefined) {
      params.append('max_depth', maxDepth.toString());
    }
    
    const response = await api.get(`/structure?${params}`);
    return response.data;
  },

  async getFolderPermissions(path: string, includeInherited = true, simplifiedSystem = true, saveForAnalysis = false): Promise<FolderPermissions> {
    const params = new URLSearchParams({ 
      path,
      include_inherited: includeInherited.toString(),
      simplified_system: simplifiedSystem.toString(),
      save_for_analysis: saveForAnalysis.toString()
    });
    
    const response = await api.get(`/permissions?${params}`);
    return response.data;
  },

  async getUserFolderAccess(username: string, domain: string, basePath?: string) {
    const params = new URLSearchParams({ username, domain });
    if (basePath) {
      params.append('base_path', basePath);
    }
    
    const response = await api.get(`/access/${username}?${params}`);
    return response.data;
  },

  async validateFolderAccess(path: string, checkWrite = false) {
    const params = new URLSearchParams({ path, check_write: checkWrite.toString() });
    const response = await api.post(`/validate?${params}`);
    return response.data;
  },

  // New ACL modification methods
  async modifyFolderPermissions(path: string, permissionRequest: PermissionRequest): Promise<PermissionResponse> {
    const params = new URLSearchParams({ path });
    const response = await api.put(`/permissions?${params}`, permissionRequest);
    return response.data;
  },

  async removeFolderPermissions(path: string, userOrGroup: string, domain: string): Promise<PermissionResponse> {
    const params = new URLSearchParams({ 
      path, 
      user_or_group: userOrGroup,
      domain 
    });
    const response = await api.delete(`/permissions?${params}`);
    return response.data;
  },

  // Group member methods
  async getGroupMembers(groupName: string, domain: string, includeNested = true): Promise<GroupMembersResponse> {
    const params = new URLSearchParams({ 
      group_name: groupName,
      domain,
      include_nested: includeNested.toString()
    });
    const response = await api.get(`/group-members?${params}`);
    return response.data;
  }
};