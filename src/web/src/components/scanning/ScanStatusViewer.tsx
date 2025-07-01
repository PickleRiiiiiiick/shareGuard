import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/utils/api';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';

interface ScanStatusViewerProps {
    jobId: number;
    onComplete?: () => void;
}

interface ScanJobStatus {
    id: number;
    status: 'running' | 'completed' | 'failed';
    start_time: string;
    end_time?: string;
    error_message?: string;
    target: {
        name: string;
        path: string;
    };
}

export function ScanStatusViewer({ jobId, onComplete }: ScanStatusViewerProps) {
    const { data: status, isLoading } = useQuery<ScanJobStatus>(
        ['scanJob', jobId],
        () => api.scan.get(`/jobs/${jobId}`),
        {
            enabled: !!jobId,
            refetchInterval: (data) =>
                data?.status === 'running' ? 5000 : false, // Poll every 5s while running
            onSuccess: (data) => {
                if (data.status !== 'running' && onComplete) {
                    // Wait 3 seconds to show the final status before closing
                    setTimeout(onComplete, 3000);
                }
            }
        }
    );

    if (isLoading || !status) {
        return (
            <div className="bg-white shadow-lg rounded-lg p-4 w-96">
                <div className="flex items-center justify-center h-24">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
                </div>
            </div>
        );
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed':
                return 'bg-green-100 text-green-800';
            case 'failed':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-blue-100 text-blue-800';
        }
    };

    return (
        <div className="bg-white shadow-lg rounded-lg p-4 w-96">
            <div className="flex justify-between items-start">
                <div>
                    <h3 className="text-sm font-medium text-gray-900">
                        {status.target.name}
                    </h3>
                    <p className="text-xs text-gray-500 mt-1">
                        {status.target.path}
                    </p>
                </div>
                {status.status !== 'running' && (
                    <button
                        onClick={onComplete}
                        className="text-gray-400 hover:text-gray-500"
                    >
                        <XMarkIcon className="h-5 w-5" />
                    </button>
                )}
            </div>

            <div className="mt-4">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(status.status)}`}>
                    {status.status.charAt(0).toUpperCase() + status.status.slice(1)}
                </span>

                <div className="mt-2 text-xs text-gray-600">
                    Started {formatDistanceToNow(new Date(status.start_time))} ago
                    {status.end_time && (
                        <div>
                            Completed {formatDistanceToNow(new Date(status.end_time))} ago
                        </div>
                    )}
                </div>

                {status.error_message && (
                    <div className="mt-2 text-xs text-red-600">
                        Error: {status.error_message}
                    </div>
                )}

                {status.status === 'running' && (
                    <div className="mt-3 w-full bg-gray-200 rounded-full h-1">
                        <div className="bg-primary-600 h-1 rounded-full animate-pulse w-1/2" />
                    </div>
                )}
            </div>
        </div>
    );
}