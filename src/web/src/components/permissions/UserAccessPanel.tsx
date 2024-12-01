import { useState } from 'react';
import { useUserFolderAccess } from '@/hooks/useFolders';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import {
    CheckCircleIcon,
    XMarkIcon,
    UserCircleIcon
} from '@heroicons/react/24/outline';
import type { PathInfo } from '@/types/folder';

interface UserAccessPanelProps {
    selectedPath?: string;
}

interface UserSearchForm {
    username: string;
    domain: string;
}

export function UserAccessPanel({ selectedPath }: UserAccessPanelProps) {
    const [searchForm, setSearchForm] = useState<UserSearchForm>({
        username: '',
        domain: '',
    });
    const [isSearching, setIsSearching] = useState(false);

    const {
        data: accessInfo,
        isLoading,
        error
    } = useUserFolderAccess(
        searchForm.username,
        searchForm.domain,
        selectedPath,
        {
            enabled: isSearching && !!searchForm.username && !!searchForm.domain
        }
    );

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setIsSearching(true);
    };

    const renderAccessStatus = (hasAccess: boolean) => {
        return hasAccess ? (
            <div className="flex items-center text-green-600">
                <CheckCircleIcon className="h-5 w-5 mr-1" />
                <span>Has Access</span>
            </div>
        ) : (
            <div className="flex items-center text-red-600">
                <XMarkIcon className="h-5 w-5 mr-1" />
                <span>No Access</span>
            </div>
        );
    };

    return (
        <div className="bg-white shadow rounded-lg">
            <div className="p-4 border-b">
                <h3 className="text-lg font-medium text-gray-900">User Access Lookup</h3>
                <p className="mt-1 text-sm text-gray-500">
                    Check user permissions for selected folder
                </p>
            </div>

            <div className="p-4">
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label htmlFor="domain" className="block text-sm font-medium text-gray-700">
                            Domain
                        </label>
                        <input
                            type="text"
                            name="domain"
                            id="domain"
                            value={searchForm.domain}
                            onChange={(e) => setSearchForm(prev => ({ ...prev, domain: e.target.value }))}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        />
                    </div>

                    <div>
                        <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                            Username
                        </label>
                        <input
                            type="text"
                            name="username"
                            id="username"
                            value={searchForm.username}
                            onChange={(e) => setSearchForm(prev => ({ ...prev, username: e.target.value }))}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={!searchForm.username || !searchForm.domain || !selectedPath}
                        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                    >
                        Check Access
                    </button>
                </form>
            </div>

            {isSearching && (
                <div className="p-4 border-t">
                    {isLoading ? (
                        <div className="flex justify-center">
                            <LoadingSpinner />
                        </div>
                    ) : error ? (
                        <div className="text-red-600 text-sm text-center">
                            Error checking access
                        </div>
                    ) : accessInfo ? (
                        <div className="space-y-4">
                            <div className="flex items-center space-x-3">
                                <UserCircleIcon className="h-10 w-10 text-gray-400" />
                                <div>
                                    <div className="font-medium">
                                        {accessInfo.domain}\{accessInfo.username}
                                    </div>
                                    <div className="text-sm text-gray-500">
                                        Access Information
                                    </div>
                                </div>
                            </div>

                            <div className="rounded-md bg-gray-50 p-4">
                                <div className="space-y-2">
                                    <div>
                                        <div className="text-sm font-medium text-gray-700">Read Access</div>
                                        {renderAccessStatus(accessInfo.access_info.readable)}
                                    </div>
                                    <div>
                                        <div className="text-sm font-medium text-gray-700">Write Access</div>
                                        {renderAccessStatus(accessInfo.access_info.writable)}
                                    </div>
                                </div>
                            </div>

                            {Object.entries(accessInfo.access_info.paths).length > 0 && (
                                <div>
                                    <h4 className="text-sm font-medium text-gray-900 mb-2">
                                        Effective Permissions
                                    </h4>
                                    <div className="space-y-2">
                                        {Object.entries(accessInfo.access_info.paths).map(([path, info]: [string, PathInfo]) => (
                                            <div key={path} className="text-sm bg-gray-50 p-3 rounded-md">
                                                <div className="font-medium">{path}</div>
                                                <div className="mt-1 flex flex-wrap gap-1">
                                                    {info.permissions.map((perm: string, index: number) => (
                                                        <span
                                                            key={index}
                                                            className="inline-flex items-center rounded-md bg-primary-50 px-2 py-1 text-xs font-medium text-primary-700"
                                                        >
                                                            {perm}
                                                        </span>
                                                    ))}
                                                </div>
                                                {info.inherited && (
                                                    <div className="mt-1 text-xs text-gray-500">
                                                        Inherited from: {info.source_path}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : null}
                </div>
            )}
        </div>
    );
}