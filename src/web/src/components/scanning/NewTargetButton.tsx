import { useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { useCreateTarget } from '@/hooks/useTargets';
import { PlusIcon } from '@heroicons/react/24/outline';
import { TargetEditForm } from './TargetEditForm';
import { ScanTarget } from '@/types/target';
import { ScanScheduleType } from '@/types/enums';
import { ScanStatusViewer } from './ScanStatusViewer';

export function NewTargetButton() {
    const [isOpen, setIsOpen] = useState(false);
    const [activeJobId, setActiveJobId] = useState<number | null>(null);
    const { mutate: createTarget, isLoading } = useCreateTarget();

    const emptyTarget: ScanTarget = {
        id: 0,
        name: '',
        path: '',
        description: '',
        department: '',
        owner: '',
        sensitivity_level: '',
        is_sensitive: false,
        scan_frequency: ScanScheduleType.DAILY,
        max_depth: 5,
        created_at: new Date().toISOString(),
        created_by: '',
    };

    const handleCreate = (data: Partial<ScanTarget>) => {
        createTarget(data as ScanTarget, {
            onSuccess: (response) => {
                // Assuming the API returns the scan job ID in the response
                if (response.job_id) {
                    setActiveJobId(response.job_id);
                }
                setIsOpen(false);
            },
        });
    };

    return (
        <>
            <button
                type="button"
                onClick={() => setIsOpen(true)}
                className="inline-flex items-center rounded-md bg-primary-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
            >
                <PlusIcon className="-ml-0.5 mr-1.5 h-5 w-5" />
                New Target
            </button>

            <Transition.Root show={isOpen} as={Fragment}>
                <Dialog as="div" className="relative z-50" onClose={setIsOpen}>
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
                                    <TargetEditForm
                                        target={emptyTarget}
                                        onSubmit={handleCreate}
                                        onCancel={() => setIsOpen(false)}
                                        isLoading={isLoading}
                                    />
                                </Dialog.Panel>
                            </Transition.Child>
                        </div>
                    </div>
                </Dialog>
            </Transition.Root>

            {/* Show scan status if there's an active job */}
            {activeJobId && (
                <div className="fixed bottom-4 right-4 z-50">
                    <ScanStatusViewer jobId={activeJobId} onComplete={() => setActiveJobId(null)} />
                </div>
            )}
        </>
    );
}