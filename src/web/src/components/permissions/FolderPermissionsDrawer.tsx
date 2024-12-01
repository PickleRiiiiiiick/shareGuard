import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useFolderPermissions } from '@/hooks/useFolders';
import { LoadingSpinner } from '@components/common/LoadingSpinner';
import { FolderPermission } from '@/types/folder';

interface FolderPermissionsDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    path: string;
}

export function FolderPermissionsDrawer({ isOpen, onClose, path }: FolderPermissionsDrawerProps) {
    const { data, isLoading } = useFolderPermissions(path, { includeInherited: true });

    const renderPermissionList = (permissions: FolderPermission[]) => {
        return permissions.map((permission, index) => (
            <div
                key={`${permission.trustee_sid}-${index}`}
                className={`p-4 ${permission.inherited ? 'bg-gray-50' : 'bg-white'}`}
            >
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-gray-900">
                            {permission.trustee_domain}\{permission.trustee_name}
                        </p>
                        <p className="text-sm text-gray-500">
                            {permission.access_type}
                        </p>
                    </div>
                    {permission.inherited && (
                        <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
                            Inherited
                        </span>
                    )}
                </div>
                <div className="mt-2">
                    <div className="flex flex-wrap gap-2">
                        {permission.permissions.map((perm, i) => (
                            <span
                                key={i}
                                className="inline-flex items-center rounded-md bg-primary-50 px-2 py-1 text-xs font-medium text-primary-700"
                            >
                                {perm}
                            </span>
                        ))}
                    </div>
                </div>
            </div>
        ));
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
                                                    Folder Permissions
                                                </Dialog.Title>
                                                <div className="ml-3 flex h-7 items-center">
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
                                            <div className="flex-1 divide-y divide-gray-200">
                                                {data?.permissions && renderPermissionList(data.permissions)}
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