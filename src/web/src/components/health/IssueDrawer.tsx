import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon, ClipboardDocumentIcon } from '@heroicons/react/24/outline';
import { ACLIssue, ISSUE_TYPE_LABELS, SEVERITY_COLORS } from '../../types/health';
import { useAlert } from '../../contexts/AlertContext';
import { ACLViewer } from './ACLViewer';

interface IssueDrawerProps {
    issue: ACLIssue | null;
    isOpen: boolean;
    onClose: () => void;
}

export function IssueDrawer({ issue, isOpen, onClose }: IssueDrawerProps) {
    const { showAlert } = useAlert();

    const handleCopyPath = async () => {
        if (issue) {
            await navigator.clipboard.writeText(issue.path);
            showAlert('Path copied to clipboard', 'success');
        }
    };

    return (
        <Transition.Root show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-50" onClose={onClose}>
                <Transition.Child
                    as={Fragment}
                    enter="ease-in-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in-out duration-300"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
                </Transition.Child>

                <div className="fixed inset-0 overflow-hidden">
                    <div className="absolute inset-0 overflow-hidden">
                        <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
                            <Transition.Child
                                as={Fragment}
                                enter="transform transition ease-in-out duration-300"
                                enterFrom="translate-x-full"
                                enterTo="translate-x-0"
                                leave="transform transition ease-in-out duration-300"
                                leaveFrom="translate-x-0"
                                leaveTo="translate-x-full"
                            >
                                <Dialog.Panel className="pointer-events-auto relative w-screen max-w-2xl">
                                    <div className="flex h-full flex-col overflow-y-scroll bg-white py-6 shadow-xl">
                                        <div className="px-4 sm:px-6">
                                            <div className="flex items-start justify-between">
                                                <Dialog.Title className="text-lg font-medium text-gray-900">
                                                    Issue Details
                                                </Dialog.Title>
                                                <div className="ml-3 flex h-7 items-center">
                                                    <button
                                                        type="button"
                                                        className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                                                        onClick={onClose}
                                                    >
                                                        <span className="sr-only">Close panel</span>
                                                        <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                        {issue && (
                                            <div className="relative mt-6 flex-1 px-4 sm:px-6">
                                                <div className="space-y-6">
                                                    <div>
                                                        <div className="flex items-center space-x-3">
                                                            <span
                                                                className={`inline-flex items-center rounded-md px-2.5 py-0.5 text-sm font-medium ${
                                                                    SEVERITY_COLORS[issue.severity].bg
                                                                } ${SEVERITY_COLORS[issue.severity].text}`}
                                                            >
                                                                {issue.severity.toUpperCase()}
                                                            </span>
                                                            <span className="text-sm text-gray-500">
                                                                {ISSUE_TYPE_LABELS[issue.type]}
                                                            </span>
                                                        </div>
                                                    </div>

                                                    <div>
                                                        <h3 className="text-sm font-medium text-gray-900">Path</h3>
                                                        <div className="mt-1 flex items-center space-x-2">
                                                            <p className="text-sm text-gray-600 break-all">{issue.path}</p>
                                                            <button
                                                                onClick={handleCopyPath}
                                                                className="flex-shrink-0 text-gray-400 hover:text-gray-500"
                                                                title="Copy path"
                                                            >
                                                                <ClipboardDocumentIcon className="h-5 w-5" />
                                                            </button>
                                                        </div>
                                                    </div>

                                                    <div>
                                                        <h3 className="text-sm font-medium text-gray-900">Description</h3>
                                                        <p className="mt-1 text-sm text-gray-600">{issue.description}</p>
                                                    </div>

                                                    <div>
                                                        <h3 className="text-sm font-bold text-gray-900 flex items-center mb-3">
                                                            <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                                                            ⚠️ Affected Users/Groups
                                                        </h3>
                                                        <div className="space-y-2">
                                                            {issue.affectedPrincipals.map((principal, index) => (
                                                                <div 
                                                                    key={index} 
                                                                    className="flex items-center p-3 bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200"
                                                                >
                                                                    <div className="flex-shrink-0 w-8 h-8 bg-red-100 rounded-full flex items-center justify-center mr-3">
                                                                        <span className="text-red-600 font-bold text-sm">
                                                                            {principal.charAt(0).toUpperCase()}
                                                                        </span>
                                                                    </div>
                                                                    <div className="flex-grow">
                                                                        <div className="font-semibold text-gray-900 text-sm">
                                                                            {principal}
                                                                        </div>
                                                                        <div className="text-xs text-gray-600">
                                                                            {principal.includes('@') ? 'User Account' : 
                                                                             principal.includes('\\') ? 'Domain Account' : 
                                                                             'Local Account'}
                                                                        </div>
                                                                    </div>
                                                                    <div className="flex-shrink-0">
                                                                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                                                            At Risk
                                                                        </span>
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>

                                                    <div>
                                                        <h3 className="text-sm font-medium text-gray-900">Detected At</h3>
                                                        <p className="mt-1 text-sm text-gray-600">
                                                            {new Date(issue.detectedAt).toLocaleString()}
                                                        </p>
                                                    </div>

                                                    {issue.details?.remediationSteps && (
                                                        <div>
                                                            <h3 className="text-sm font-medium text-gray-900">Remediation Steps</h3>
                                                            <ol className="mt-1 list-decimal list-inside space-y-1">
                                                                {issue.details.remediationSteps.map((step, index) => (
                                                                    <li key={index} className="text-sm text-gray-600">
                                                                        {step}
                                                                    </li>
                                                                ))}
                                                            </ol>
                                                        </div>
                                                    )}

                                                    {/* Only show Current ACL if it contains meaningful data */}
                                                    {issue.details?.currentACL && 
                                                     typeof issue.details.currentACL === 'object' && 
                                                     Object.keys(issue.details.currentACL).length > 0 && 
                                                     !(typeof issue.details.currentACL === 'string' && issue.details.currentACL.trim().length < 10) && (
                                                        <ACLViewer 
                                                            aclData={issue.details.currentACL} 
                                                            title="📋 Current ACL Details" 
                                                        />
                                                    )}

                                                    {/* Show recommendations if available */}
                                                    {issue.details?.recommendedACL && (
                                                        <ACLViewer 
                                                            aclData={issue.details.recommendedACL} 
                                                            title="💡 Recommended Solutions" 
                                                        />
                                                    )}
                                                </div>
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