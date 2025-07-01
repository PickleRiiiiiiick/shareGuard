import { useState } from 'react';
import { ScanTarget } from '@/types/target';
import { formatDistanceToNow } from 'date-fns';
import {
    CalendarIcon,
    CheckCircleIcon,
    ExclamationCircleIcon,
    FolderIcon,
} from '@heroicons/react/24/outline';
import { TargetDetailsModal } from './TargetDetailsModal';

interface ScanTargetRowProps {
    target: ScanTarget;
}

export function ScanTargetRow({ target }: ScanTargetRowProps) {
    const [showDetails, setShowDetails] = useState(false);

    const getStatusIcon = () => {
        if (!target.last_scan_time) {
            return <CalendarIcon className="h-5 w-5 text-gray-400" />;
        }
        return target.is_sensitive ? (
            <ExclamationCircleIcon className="h-5 w-5 text-yellow-400" />
        ) : (
            <CheckCircleIcon className="h-5 w-5 text-green-400" />
        );
    };

    return (
        <>
            <li>
                <div
                    className="block hover:bg-gray-50 cursor-pointer"
                    onClick={() => setShowDetails(true)}
                >
                    <div className="px-4 py-4 sm:px-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center min-w-0">
                                <div className="flex-shrink-0">
                                    <FolderIcon className="h-6 w-6 text-gray-400" />
                                </div>
                                <div className="min-w-0 flex-1 px-4">
                                    <p className="text-sm font-medium text-primary-600 truncate">
                                        {target.name}
                                    </p>
                                    <p className="mt-1 text-sm text-gray-500 truncate">
                                        {target.path}
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center space-x-4">
                                <div className="hidden md:block">
                                    <div>
                                        <div className="flex items-center space-x-2">
                                            <p className="text-sm text-gray-900">
                                                {target.scan_frequency.toUpperCase()}
                                            </p>
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                                target.scan_frequency === 'disabled' 
                                                    ? 'bg-red-100 text-red-800' 
                                                    : 'bg-green-100 text-green-800'
                                            }`}>
                                                {target.scan_frequency === 'disabled' ? 'Inactive' : 'Active'}
                                            </span>
                                        </div>
                                        {target.last_scan_time && (
                                            <p className="mt-1 text-sm text-gray-500">
                                                Last scan {formatDistanceToNow(new Date(target.last_scan_time))} ago
                                            </p>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center">
                                    {getStatusIcon()}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </li>

            <TargetDetailsModal
                isOpen={showDetails}
                onClose={() => setShowDetails(false)}
                target={target}
            />
        </>
    );
}