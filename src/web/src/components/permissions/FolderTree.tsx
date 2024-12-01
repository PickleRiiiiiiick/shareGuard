import { useState, useCallback } from 'react';
import { useFolderStructure } from '@/hooks/useFolders';
import { FolderStructure, FolderTreeOptions } from '@/types/folder';
import { LoadingSpinner } from '@components/common/LoadingSpinner';
import {
    ChevronRightIcon,
    ChevronDownIcon,
    FolderIcon,
    DocumentIcon,
    ShieldExclamationIcon,
} from '@heroicons/react/24/outline';
import { FolderPermissionsDrawer } from './FolderPermissionsDrawer';
import clsx from 'clsx';

interface FolderTreeProps {
    rootPath: string;
    options?: FolderTreeOptions;
    onFolderSelect?: (folder: FolderStructure) => void;
}

export function FolderTree({ rootPath, options, onFolderSelect }: FolderTreeProps) {
    const [expandedPaths, setExpandedPaths] = useState<Set<string>>(
        new Set(options?.expandedPaths || [])
    );
    const [selectedPath, setSelectedPath] = useState<string | null>(null);
    const [showPermissions, setShowPermissions] = useState(false);

    const { data: structure, isLoading, error } = useFolderStructure(rootPath, options);

    const handleToggle = useCallback((path: string) => {
        setExpandedPaths(prev => {
            const next = new Set(prev);
            if (next.has(path)) {
                next.delete(path);
            } else {
                next.add(path);
            }
            return next;
        });
    }, []);

    const handleSelect = useCallback((folder: FolderStructure) => {
        setSelectedPath(folder.path);
        onFolderSelect?.(folder);
    }, [onFolderSelect]);

    const renderItem = useCallback((item: FolderStructure, depth: number = 0) => {
        const isExpanded = expandedPaths.has(item.path);
        const isSelected = selectedPath === item.path;
        const hasChildren = item.children && item.children.length > 0;

        return (
            <div key={item.path}>
                <div
                    className={clsx(
                        'group flex items-center py-1 px-2 hover:bg-gray-100 cursor-pointer',
                        isSelected && 'bg-primary-50',
                        depth > 0 && 'ml-6'
                    )}
                >
                    {item.type === 'folder' && (
                        <button
                            onClick={() => handleToggle(item.path)}
                            className="p-1 hover:bg-gray-200 rounded"
                        >
                            {hasChildren ? (
                                isExpanded ? (
                                    <ChevronDownIcon className="h-4 w-4 text-gray-500" />
                                ) : (
                                    <ChevronRightIcon className="h-4 w-4 text-gray-500" />
                                )
                            ) : (
                                <span className="w-4" />
                            )}
                        </button>
                    )}

                    <div
                        className="flex-1 flex items-center gap-2 py-1"
                        onClick={() => handleSelect(item)}
                    >
                        {item.type === 'folder' ? (
                            <FolderIcon className="h-5 w-5 text-gray-400" />
                        ) : (
                            <DocumentIcon className="h-5 w-5 text-gray-400" />
                        )}
                        <span className="text-sm text-gray-900">{item.name}</span>
                    </div>

                    {item.permissions && (
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                setSelectedPath(item.path);
                                setShowPermissions(true);
                            }}
                            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-200 rounded"
                        >
                            <ShieldExclamationIcon className="h-4 w-4 text-gray-500" />
                        </button>
                    )}
                </div>

                {isExpanded && hasChildren && (
                    <div className="ml-4">
                        {item.children!.map(child => renderItem(child, depth + 1))}
                    </div>
                )}
            </div>
        );
    }, [expandedPaths, selectedPath, handleToggle, handleSelect]);

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
                Error loading folder structure
            </div>
        );
    }

    if (!structure) {
        return (
            <div className="text-center text-gray-500 p-4">
                No folder structure available
            </div>
        );
    }

    return (
        <div className="relative">
            <div className="border rounded-lg bg-white">
                <div className="p-4">
                    <h3 className="text-lg font-medium text-gray-900">Folder Structure</h3>
                    <p className="mt-1 text-sm text-gray-500">
                        Browse folders and manage permissions
                    </p>
                </div>

                <div className="border-t">
                    <div className="p-4">
                        {renderItem(structure)}
                    </div>
                </div>
            </div>

            {selectedPath && (
                <FolderPermissionsDrawer
                    isOpen={showPermissions}
                    onClose={() => setShowPermissions(false)}
                    path={selectedPath}
                />
            )}
        </div>
    );
}