import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon, PencilIcon } from '@heroicons/react/24/outline';
import { ScanTarget } from '@/types/target';
import { useTargetStats, useUpdateTarget, useDeleteTarget } from '@/hooks/useTargets';
import { format } from 'date-fns';
import { LoadingSpinner } from '@components/common/LoadingSpinner';
import { useState } from 'react';
import { TargetEditForm } from './TargetEditForm';

interface TargetDetailsModalProps {
    isOpen: boolean;
    onClose: () => void;
    target: ScanTarget;
}

export function TargetDetailsModal({ isOpen, onClose, target }: TargetDetailsModalProps) {
    const [isEditing, setIsEditing] = useState(false);
    const { data: stats, isLoading: statsLoading } = useTargetStats(target.id);
    const { mutate: updateTarget, isLoading: updateLoading } = useUpdateTarget();
    const { mutate: deleteTarget, isLoading: deleteLoading } = useDeleteTarget();

    const handleDelete = async () => {
        if (window.confirm('Are you sure you want to delete this target? This action cannot be undone.')) {
            deleteTarget(target.id, {
                onSuccess: () => {
                    onClose();
                },
            });
        }
    };

    const handleUpdate = (updatedData: Partial<ScanTarget>) => {
        updateTarget(
            { id: target.id, data: updatedData },
            {
                onSuccess: () => {
                    setIsEditing(false);
                },
            }
        );
    };

    return (
        <Transition.Root show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-50" onClose={onClose}>
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
                </Transition.Child>

                <div className="fixed inset-0 z-10 overflow-y-auto">
                    <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                        <Transition.Child
                            as={Fragment}
                            enter="ease-out duration-300"
                            enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
                            enterTo="opacity-100 translate-y-0 sm:scale-100"
                            leave="ease-in duration-200"
                            leaveFrom="opacity-100 translate-y-0 sm:scale-100"
                            leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
                        >
                            <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl sm:p-6">
                                <div className="absolute right-0 top-0 hidden pr-4 pt-4 sm:block">
                                    <button
                                        type="button"
                                        className="rounded-md bg-white text-gray-400 hover:text-gray-500"
                                        onClick={onClose}
                                    >
                                        <span className="sr-only">Close</span>
                                        <XMarkIcon className="h-6 w-6" />
                                    </button>
                                </div>

                                {isEditing ? (
                                    <TargetEditForm
                                        target={target}
                                        onSubmit={handleUpdate}
                                        onCancel={() => setIsEditing(false)}
                                        isLoading={updateLoading}
                                    />
                                ) : (
                                    <div className="space-y-6">
                                        <div>
                                            <div className="flex items-center justify-between">
                                                <Dialog.Title className="text-lg font-semibold text-gray-900">
                                                    Target Details
                                                </Dialog.Title>
                                                <button
                                                    type="button"
                                                    className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700"
                                                    onClick={() => setIsEditing(true)}
                                                >
                                                    <PencilIcon className="h-4 w-4 mr-1" />
                                                    Edit
                                                </button>
                                            </div>

                                            <dl className="mt-6 grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                                                <div>
                                                    <dt className="text-sm font-medium text-gray-500">Name</dt>
                                                    <dd className="mt-1 text-sm text-gray-900">{target.name}</dd>
                                                </div>
                                                <div>
                                                    <dt className="text-sm font-medium text-gray-500">Path</dt>
                                                    <dd className="mt-1 text-sm text-gray-900">{target.path}</dd>
                                                </div>
                                                <div>
                                                    <dt className="text-sm font-medium text-gray-500">Department</dt>
                                                    <dd className="mt-1 text-sm text-gray-900">{target.department || 'N/A'}</dd>
                                                </div>
                                                <div>
                                                    <dt className="text-sm font-medium text-gray-500">Owner</dt>
                                                    <dd className="mt-1 text-sm text-gray-900">{target.owner || 'N/A'}</dd>
                                                </div>
                                                <div>
                                                    <dt className="text-sm font-medium text-gray-500">Scan Frequency</dt>
                                                    <dd className="mt-1 text-sm text-gray-900">
                                                        {target.scan_frequency.charAt(0).toUpperCase() + target.scan_frequency.slice(1)}
                                                    </dd>
                                                </div>
                                                <div>
                                                    <dt className="text-sm font-medium text-gray-500">Last Scan</dt>
                                                    <dd className="mt-1 text-sm text-gray-900">
                                                        {target.last_scan_time
                                                            ? format(new Date(target.last_scan_time), 'PPpp')
                                                            : 'Never'}
                                                    </dd>
                                                </div>
                                            </dl>
                                        </div>

                                        {statsLoading ? (
                                            <div className="flex justify-center py-4">
                                                <LoadingSpinner />
                                            </div>
                                        ) : stats && (
                                            <div>
                                                <h3 className="text-sm font-medium text-gray-900">Scan Statistics</h3>
                                                <dl className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
                                                    <div className="bg-gray-50 px-4 py-5 rounded-lg">
                                                        <dt className="text-sm font-medium text-gray-500">Total Scans</dt>
                                                        <dd className="mt-1 text-2xl font-semibold text-gray-900">
                                                            {stats.total_scans}
                                                        </dd>
                                                    </div>
                                                    <div className="bg-gray-50 px-4 py-5 rounded-lg">
                                                        <dt className="text-sm font-medium text-gray-500">Success Rate</dt>
                                                        <dd className="mt-1 text-2xl font-semibold text-gray-900">
                                                            {((stats.successful_scans / stats.total_scans) * 100).toFixed(1)}%
                                                        </dd>
                                                    </div>
                                                    <div className="bg-gray-50 px-4 py-5 rounded-lg">
                                                        <dt className="text-sm font-medium text-gray-500">Avg. Duration</dt>
                                                        <dd className="mt-1 text-2xl font-semibold text-gray-900">
                                                            {stats.average_duration ? `${stats.average_duration}s` : 'N/A'}
                                                        </dd>
                                                    </div>
                                                </dl>
                                            </div>
                                        )}

                                        <div className="mt-6 flex justify-end space-x-3">
                                            <button
                                                type="button"
                                                className="inline-flex justify-center rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500"
                                                onClick={handleDelete}
                                                disabled={deleteLoading}
                                            >
                                                {deleteLoading ? 'Deleting...' : 'Delete Target'}
                                            </button>
                                            <button
                                                type="button"
                                                className="inline-flex justify-center rounded-md bg-gray-100 px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm hover:bg-gray-200"
                                                onClick={onClose}
                                            >
                                                Close
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition.Root>
    );
}