import { useState } from 'react';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import { useModifyFolderPermissions, useRemoveFolderPermissions } from '@/hooks/useFolders';
import type { PermissionRequest } from '@/api/folders';

interface ACLEditFormProps {
  path: string;
  onPermissionChange?: () => void;
}

const PERMISSION_OPTIONS = [
  { value: 'read', label: 'Read' },
  { value: 'write', label: 'Write' },
  { value: 'execute', label: 'Execute' },
  { value: 'modify', label: 'Modify' },
  { value: 'full_control', label: 'Full Control' },
  { value: 'list_folder', label: 'List Folder' },
  { value: 'create_files', label: 'Create Files' },
  { value: 'create_folders', label: 'Create Folders' },
];

interface ACE {
  trustee: {
    full_name: string;
    domain: string;
    name: string;
    sid: string;
  };
  type: string;
  inherited: boolean;
  is_system: boolean;
  permissions: any;
}

interface ACLEditFormProps {
  path: string;
  aces?: ACE[];
  onPermissionChange?: () => void;
}

export function ACLEditForm({ path, aces = [], onPermissionChange }: ACLEditFormProps) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newPermission, setNewPermission] = useState<PermissionRequest>({
    user_or_group: '',
    domain: '',
    permissions: [],
    access_type: 'allow'
  });

  const modifyPermissionsMutation = useModifyFolderPermissions();
  const removePermissionsMutation = useRemoveFolderPermissions();

  const handleAddPermission = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newPermission.user_or_group || !newPermission.domain || newPermission.permissions.length === 0) {
      return;
    }

    try {
      await modifyPermissionsMutation.mutateAsync({
        path,
        permissionRequest: newPermission
      });
      
      // Reset form
      setNewPermission({
        user_or_group: '',
        domain: '',
        permissions: [],
        access_type: 'allow'
      });
      setShowAddForm(false);
      onPermissionChange?.();
    } catch (error) {
      console.error('Failed to add permission:', error);
    }
  };

  const handleRemovePermission = async (ace: ACE) => {
    if (ace.inherited || ace.is_system) {
      return; // Don't allow removal of inherited or system permissions
    }

    try {
      await removePermissionsMutation.mutateAsync({
        path,
        userOrGroup: ace.trustee.name,
        domain: ace.trustee.domain
      });
      onPermissionChange?.();
    } catch (error) {
      console.error('Failed to remove permission:', error);
    }
  };

  const handlePermissionToggle = (permission: string) => {
    setNewPermission(prev => ({
      ...prev,
      permissions: prev.permissions.includes(permission)
        ? prev.permissions.filter(p => p !== permission)
        : [...prev.permissions, permission]
    }));
  };

  return (
    <div className="space-y-4">
      {/* Add Permission Button */}
      <div className="flex justify-between items-center">
        <h4 className="text-sm font-medium text-gray-900">Manage Permissions</h4>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors"
        >
          <PlusIcon className="h-4 w-4" />
          Add Permission
        </button>
      </div>

      {/* Add Permission Form */}
      {showAddForm && (
        <div className="border rounded-lg p-4 bg-gray-50">
          <form onSubmit={handleAddPermission} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                User/Group Name
              </label>
              <input
                type="text"
                value={newPermission.user_or_group}
                onChange={(e) => setNewPermission(prev => ({ ...prev, user_or_group: e.target.value }))}
                placeholder="e.g., john.doe"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Domain
              </label>
              <input
                type="text"
                value={newPermission.domain}
                onChange={(e) => setNewPermission(prev => ({ ...prev, domain: e.target.value }))}
                placeholder="e.g., MYDOMAIN"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Access Type
              </label>
              <select
                value={newPermission.access_type}
                onChange={(e) => setNewPermission(prev => ({ ...prev, access_type: e.target.value as 'allow' | 'deny' }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="allow">Allow</option>
                <option value="deny">Deny</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Permissions
              </label>
              <div className="grid grid-cols-2 gap-2">
                {PERMISSION_OPTIONS.map((permission) => (
                  <label key={permission.value} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={newPermission.permissions.includes(permission.value)}
                      onChange={() => handlePermissionToggle(permission.value)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">{permission.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={modifyPermissionsMutation.isLoading}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {modifyPermissionsMutation.isLoading ? 'Adding...' : 'Add Permission'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Existing Permissions List with Remove Option */}
      {aces.length > 0 && (
        <div className="space-y-2">
          <h5 className="text-xs font-medium text-gray-600 uppercase tracking-wide">
            Current Permissions
          </h5>
          {aces.map((ace, index) => (
            <div
              key={`${ace.trustee.sid}-${index}`}
              className={`flex items-center justify-between p-3 rounded-md ${
                ace.inherited ? 'bg-gray-50' : 'bg-white border'
              }`}
            >
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900">
                    {ace.trustee.full_name}
                  </span>
                  {ace.inherited && (
                    <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                      Inherited
                    </span>
                  )}
                  {ace.is_system && (
                    <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                      System
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {ace.type} - {Object.values(ace.permissions || {}).flat().join(', ')}
                </p>
              </div>
              
              {!ace.inherited && !ace.is_system && (
                <button
                  onClick={() => handleRemovePermission(ace)}
                  disabled={removePermissionsMutation.isLoading}
                  className="p-1 text-red-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                  title="Remove permission"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}