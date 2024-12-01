import { useState } from 'react';
import { FolderTree } from '@components/permissions/FolderTree';
import { UserAccessPanel } from '@components/permissions/UserAccessPanel';
import { FolderStructure } from '@/types/folder';

export function PermissionsPage() {
    const [selectedFolder, setSelectedFolder] = useState<FolderStructure | null>(null);

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-semibold text-gray-900">Permissions Management</h1>
                <p className="mt-2 text-sm text-gray-500">
                    Browse folders and manage permissions across your file system.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                    <FolderTree
                        rootPath="C:\"
                        options={{
                            showFiles: false,
                            showPermissions: true,
                            maxDepth: 3
                        }}
                        onFolderSelect={setSelectedFolder}
                    />
                </div>
                <div>
                    <UserAccessPanel
                        selectedPath={selectedFolder?.path}
                    />
                </div>
            </div>
        </div>
    );
}