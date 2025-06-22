import { Fragment, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon, PencilIcon, UserGroupIcon } from '@heroicons/react/24/outline';
import { useFolderPermissions } from '@/hooks/useFolders';
import { LoadingSpinner } from '@components/common/LoadingSpinner';
import { ACLEditForm } from './ACLEditForm';
import { GroupMemberViewer } from './GroupMemberViewer';

interface FolderPermissionsDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    path: string;
}

interface ACE {
    trustee: {
        full_name: string;
        domain: string;
        name: string;
        sid: string;
        account_type?: string;
    };
    type: string;
    inherited: boolean;
    is_system: boolean;
    permissions: {
        Basic?: string[];
        Advanced?: string[];
        Directory?: string[];
    };
}

interface PermissionsResponse {
    permissions: {
        aces: ACE[];
        owner: any;
        primary_group: any;
        scan_time: string;
        success: boolean;
    };
}

export function FolderPermissionsDrawer({ isOpen, onClose, path }: FolderPermissionsDrawerProps) {
    const [showEditMode, setShowEditMode] = useState(false);
    const [selectedGroup, setSelectedGroup] = useState<{ name: string; domain: string } | null>(null);
    const { data, isLoading, refetch } = useFolderPermissions(path, { includeInherited: true }) as { data: PermissionsResponse | undefined, isLoading: boolean, refetch: () => void };
    
    console.log('Full API data:', data);
    console.log('Data permissions:', data?.permissions);
    console.log('Data permissions aces:', data?.permissions?.aces);

    const handlePermissionChange = () => {
        refetch(); // Refresh permissions data
    };

    const isGroup = (trustee: any) => {
        // First check if the backend provided type information
        if (trustee.account_type) {
            const accountType = trustee.account_type.toLowerCase();
            return accountType.includes('group') || accountType.includes('alias');
        }
        
        // Fall back to pattern-based detection if no type info
        if (!trustee.full_name && !trustee.name) return false;
        
        const fullName = trustee.full_name || '';
        const name = trustee.name || '';
        
        // Check for explicit group indicators
        const groupIndicators = [
            'Domain Admins', 'Domain Users', 'Enterprise Admins', 'Schema Admins',
            'Domain Controllers', 'Cert Publishers', 'DNS Admins', 'Group Policy',
            'Exchange', 'Backup Operators', 'Server Operators', 'Account Operators',
            'Print Operators', 'Replicator', 'DHCP', 'Performance', 'Remote Desktop',
            'IIS_', 'SQLServer', 'Distributed COM Users', 'Network Configuration',
            'Event Log Readers', 'Hyper-V', 'Terminal Server', 'Cryptographic Operators'
        ];
        
        // Check for group patterns in name
        const isGroupByName = groupIndicators.some(indicator => 
            fullName.includes(indicator) || name.includes(indicator)
        );
        
        // Check for common group suffixes/prefixes
        const groupPatterns = [
            /\b(group|grp|admin|admins|users|operators|service)\b/i,
            /^(BUILTIN|NT AUTHORITY)\\.*$/,
            /.*\s(Group|Groups|Admin|Admins|Users|Operators)$/i,
            /^[A-Z]{2,}\\_/  // Service accounts like IIS_IUSRS
        ];
        
        const isGroupByPattern = groupPatterns.some(pattern => 
            pattern.test(fullName) || pattern.test(name)
        );
        
        // Special case for well-known groups that might not follow patterns
        const wellKnownGroups = [
            'Users', 'Administrators', 'Power Users', 'Guests', 'Everyone',
            'Authenticated Users', 'INTERACTIVE', 'NETWORK', 'SERVICE'
        ];
        
        const isWellKnownGroup = wellKnownGroups.some(group =>
            name === group || fullName.endsWith(`\\${group}`)
        );
        
        return isGroupByName || isGroupByPattern || isWellKnownGroup;
    };

    const handleGroupClick = (trustee: any) => {
        // Check if this is a group using improved detection
        if (isGroup(trustee) && trustee.domain && trustee.name) {
            setSelectedGroup({ 
                name: trustee.name, 
                domain: trustee.domain 
            });
        }
    };

    const renderPermissionList = (aces: ACE[]) => {
        console.log('Rendering ACEs:', aces);
        
        return aces.map((ace, index) => {
            console.log('ACE:', ace);
            console.log('ACE permissions:', ace.permissions);
            
            return (
                <div
                    key={`${ace.trustee.sid}-${index}`}
                    className={`p-4 ${ace.inherited ? 'bg-gray-50' : 'bg-white'}`}
                >
                    <div className="flex items-center justify-between">
                        <div 
                            className={`cursor-pointer flex-1 ${
                                isGroup(ace.trustee) ? 'hover:bg-blue-50 rounded-md p-1 -m-1' : ''
                            }`}
                            onClick={() => handleGroupClick(ace.trustee)}
                        >
                            <div className="flex items-center gap-2">
                                <p className={`text-sm font-medium transition-colors ${
                                    isGroup(ace.trustee) 
                                        ? 'text-blue-900 hover:text-blue-700 cursor-pointer' 
                                        : 'text-gray-900'
                                }`}>
                                    {ace.trustee.full_name}
                                </p>
                                {/* Show group icon for all detected groups */}
                                {isGroup(ace.trustee) && (
                                    <UserGroupIcon className="h-4 w-4 text-blue-500" />
                                )}
                                {/* Show clickable indicator for groups */}
                                {isGroup(ace.trustee) && ace.trustee.domain && ace.trustee.name && (
                                    <span className="text-xs bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded cursor-pointer">
                                        Click to view members
                                    </span>
                                )}
                            </div>
                            <p className="text-sm text-gray-500">
                                {ace.type}
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            {ace.inherited && (
                                <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
                                    Inherited
                                </span>
                            )}
                        </div>
                    </div>
                    <div className="mt-2">
                        <div className="space-y-2">
                            {Object.entries(ace.permissions || {}).map(([category, perms]) => {
                                console.log(`Category: ${category}, Perms:`, perms, 'Type:', typeof perms, 'Array?', Array.isArray(perms));
                                
                                // Ensure perms is an array
                                const permArray = Array.isArray(perms) ? perms : (perms ? [perms] : []);
                                
                                return permArray.length > 0 && (
                                    <div key={category}>
                                        <p className="text-xs font-medium text-gray-600 mb-1">{category}:</p>
                                        <div className="flex flex-wrap gap-1">
                                            {permArray.map((perm, i) => (
                                                <span
                                                    key={i}
                                                    className="inline-flex items-center rounded-md bg-primary-50 px-2 py-1 text-xs font-medium text-primary-700"
                                                >
                                                    {String(perm)}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            );
        });
    };

    return (
        <Transition.Root show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-50" onClose={onClose}>
                <div className="fixed inset-0" />

                <div className="fixed inset-0 overflow-hidden">
                    <div className="absolute inset-0 overflow-hidden">
                        <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10 sm:pl-16">
                            <Transition.Child
                                as={Fragment}
                                enter="transform transition ease-in-out duration-500 sm:duration-700"
                                enterFrom="translate-x-full"
                                enterTo="translate-x-0"
                                leave="transform transition ease-in-out duration-500 sm:duration-700"
                                leaveFrom="translate-x-0"
                                leaveTo="translate-x-full"
                            >
                                <Dialog.Panel className="pointer-events-auto w-screen max-w-md">
                                    <div className="flex h-full flex-col overflow-y-scroll bg-white shadow-xl">
                                        <div className="bg-primary-700 py-6 px-4 sm:px-6">
                                            <div className="flex items-center justify-between">
                                                <Dialog.Title className="text-base font-semibold leading-6 text-white">
                                                    {selectedGroup 
                                                        ? `Group Members: ${selectedGroup.name}`
                                                        : `Folder Permissions ${showEditMode ? '(Edit Mode)' : ''}`
                                                    }
                                                </Dialog.Title>
                                                <div className="ml-3 flex h-7 items-center gap-2">
                                                    <button
                                                        type="button"
                                                        onClick={() => {
                                                            console.log('Edit button clicked, current showEditMode:', showEditMode);
                                                            setShowEditMode(!showEditMode);
                                                        }}
                                                        className="rounded-md bg-primary-600 text-white hover:bg-primary-500 p-1 focus:outline-none focus:ring-2 focus:ring-white"
                                                        title={showEditMode ? "View Mode" : "Edit Mode"}
                                                    >
                                                        <PencilIcon className="h-4 w-4" />
                                                    </button>
                                                    <button
                                                        type="button"
                                                        className="rounded-md bg-primary-700 text-primary-200 hover:text-white focus:outline-none focus:ring-2 focus:ring-white"
                                                        onClick={onClose}
                                                    >
                                                        <span className="sr-only">Close panel</span>
                                                        <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                                                    </button>
                                                </div>
                                            </div>
                                            <div className="mt-1">
                                                <p className="text-sm text-primary-200">
                                                    {path}
                                                </p>
                                            </div>
                                        </div>

                                        {isLoading ? (
                                            <div className="flex-1 flex items-center justify-center">
                                                <LoadingSpinner />
                                            </div>
                                        ) : (
                                            <div className="flex-1">
                                                {selectedGroup ? (
                                                    <div className="p-4">
                                                        <GroupMemberViewer 
                                                            groupName={selectedGroup.name}
                                                            domain={selectedGroup.domain}
                                                            onClose={() => setSelectedGroup(null)}
                                                        />
                                                    </div>
                                                ) : showEditMode ? (
                                                    <div className="p-4">
                                                        <ACLEditForm 
                                                            path={path} 
                                                            aces={data?.permissions?.aces || []}
                                                            onPermissionChange={handlePermissionChange}
                                                        />
                                                    </div>
                                                ) : (
                                                    <div className="divide-y divide-gray-200">
                                                        {data?.permissions?.aces && renderPermissionList(data.permissions.aces)}
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </Dialog.Panel>
                            </Transition.Child>
                        </div>
                    </div>
                </div>
            </Dialog>
        </Transition.Root>
    );
}