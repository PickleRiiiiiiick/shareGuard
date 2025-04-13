// src/web/src/components/permissions/FolderTree.tsx
import { useState, useCallback, useEffect } from 'react';
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
    const [customRootPath, setCustomRootPath] = useState(rootPath);
    const [currentRootPath, setCurrentRootPath] = useState(rootPath);
    const [expandedPaths, setExpandedPaths] = useState<Set<string>>(
        new Set(options?.expandedPaths || [])
    );
    const [selectedPath, setSelectedPath] = useState<string | null>(null);
    const [showPermissions, setShowPermissions] = useState(false);

    const { data, isLoading, error, refetch } = useFolderStructure(currentRootPath, options);
    
    // Extract structure from response if needed
    const structure = data?.structure || data;

    const handleBrowse = (e: React.FormEvent) => {
        e.preventDefault();
        setCurrentRootPath(customRootPath);
        refetch();
    };

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

    return (
        <div className="relative">
            <div className="border rounded-lg bg-white">
                <div className="p-4">
                    <h3 className="text-lg font-medium text-gray-900">Folder Structure</h3>
                    <p className="mt-1 text-sm text-gray-500">
                        Browse folders and manage permissions
                    </p>

                    <div className="mt-4">
                        <form onSubmit={handleBrowse}>
                            <label className="block text-sm font-medium text-gray-700">Root Path:</label>
                            <div className="mt-1 flex rounded-md shadow-sm">
                                <input
                                    type="text"
                                    value={customRootPath}
                                    onChange={(e) => setCustomRootPath(e.target.value)}
                                    className="flex-1 min-w-0 block w-full px-3 py-2 rounded-md border border-gray-300 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                                    placeholder="Enter folder path (e.g., C:\ShareGuardTest\IT)"
                                />
                                <button
                                    type="submit"
                                    className="ml-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                                >
                                    Browse
                                </button>
                            </div>
                        </form>
                    </div>
                </div>

                <div className="border-t">
                    <div className="p-4">
                        {isLoading ? (
                            <div className="flex justify-center items-center h-32">
                                <LoadingSpinner />
                            </div>
                        ) : error ? (
                            <div className="text-center text-red-600 p-4">
                                Error loading folder structure. Please check the path and try again.
                            </div>
                        ) : !structure ? (
                            <div className="text-center text-gray-500 p-4">
                                No folder structure available. Enter a valid path and click Browse.
                            </div>
                        ) : (
                            renderItem(structure)
                        )}
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