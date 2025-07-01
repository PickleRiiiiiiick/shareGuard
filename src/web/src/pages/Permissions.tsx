import { useState } from 'react';
import { FolderTree } from '@components/permissions/FolderTree';
import { UserAccessPanel } from '@components/permissions/UserAccessPanel';
import { LoadingSpinner } from '@components/common/LoadingSpinner';
import { PermissionNotificationTest } from '@components/permissions/PermissionNotificationTest';
import { FolderStructure } from '@/types/folder';
import { ScanTarget } from '@/types/target';
import { useTargets } from '@/hooks/useTargets';
import { FolderIcon } from '@heroicons/react/24/outline';

export function PermissionsPage() {
    const [selectedFolder, setSelectedFolder] = useState<FolderStructure | null>(null);
    const [selectedTarget, setSelectedTarget] = useState<ScanTarget | null>(null);
    const { data: targets, isLoading, error } = useTargets();

    const handleTargetSelect = (target: ScanTarget) => {
        setSelectedTarget(target);
        setSelectedFolder(null);
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <LoadingSpinner />
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center text-red-600 p-4">
                Error loading scan targets
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-semibold text-gray-900">Permissions Management</h1>
                <p className="mt-2 text-sm text-gray-500">
                    Browse scan targets and manage permissions for monitored folders.
                </p>
            </div>

            {/* Temporary notification test */}
            <PermissionNotificationTest />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                    {!selectedTarget ? (
                        <div className="border rounded-lg bg-white">
                            <div className="p-4">
                                <h3 className="text-lg font-medium text-gray-900">Scan Targets</h3>
                                <p className="mt-1 text-sm text-gray-500">
                                    Select a scan target to view its folder structure and permissions
                                </p>
                            </div>
                            <div className="border-t">
                                {targets && targets.length > 0 ? (
                                    <div className="divide-y">
                                        {targets.map((target) => (
                                            <div
                                                key={target.id}
                                                onClick={() => handleTargetSelect(target)}
                                                className="p-4 hover:bg-gray-50 cursor-pointer flex items-center gap-3"
                                            >
                                                <FolderIcon className="h-5 w-5 text-gray-400" />
                                                <div>
                                                    <h4 className="font-medium text-gray-900">{target.name}</h4>
                                                    <p className="text-sm text-gray-500">{target.path}</p>
                                                    {target.description && (
                                                        <p className="text-xs text-gray-400 mt-1">{target.description}</p>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="p-8 text-center">
                                        <FolderIcon className="mx-auto h-12 w-12 text-gray-400" />
                                        <h3 className="mt-2 text-sm font-medium text-gray-900">No scan targets</h3>
                                        <p className="mt-1 text-sm text-gray-500">
                                            Add scan targets from the Dashboard to view their permissions here.
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => setSelectedTarget(null)}
                                    className="text-sm text-blue-600 hover:text-blue-800"
                                >
                                    ← Back to targets
                                </button>
                                <span className="text-sm text-gray-500">
                                    / {selectedTarget.name}
                                </span>
                            </div>
                            <FolderTree
                                rootPath={selectedTarget.path}
                                options={{
                                    showFiles: false,
                                    showPermissions: true,
                                    maxDepth: 6
                                }}
                                onFolderSelect={setSelectedFolder}
                            />
                        </div>
                    )}
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