import { useActiveScanJobs, useScanStats } from '@/hooks/useScan';
import { LoadingSpinner } from '@components/common/LoadingSpinner';
import { ClockIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';

export function ScanStatusWidget() {
    const { data: stats, isLoading: statsLoading } = useScanStats();
    const { data: activeJobs, isLoading: jobsLoading } = useActiveScanJobs();

    if (statsLoading || jobsLoading) {
        return (
            <div className="rounded-lg bg-white p-6 shadow">
                <div className="flex justify-center items-center h-48">
                    <LoadingSpinner />
                </div>
            </div>
        );
    }

    return (
        <div className="rounded-lg bg-white p-6 shadow">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium text-gray-900">Scan Status</h2>
                <div className="flex items-center gap-2">
                    {activeJobs && activeJobs.length > 0 && (
                        <span className="flex items-center gap-1">
                            <span className="relative flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-primary-500"></span>
                            </span>
                            <span className="text-sm text-gray-500">{activeJobs.length} Active Scans</span>
                        </span>
                    )}
                </div>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-3">
                <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <CheckCircleIcon className="h-6 w-6 text-green-500" />
                        </div>
                        <div className="ml-3">
                            <h3 className="text-sm font-medium text-gray-900">Successful Scans</h3>
                            <p className="text-2xl font-semibold text-gray-700">{stats?.jobs.successful || 0}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <XCircleIcon className="h-6 w-6 text-red-500" />
                        </div>
                        <div className="ml-3">
                            <h3 className="text-sm font-medium text-gray-900">Failed Scans</h3>
                            <p className="text-2xl font-semibold text-gray-700">{stats?.jobs.failed || 0}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <ClockIcon className="h-6 w-6 text-primary-500" />
                        </div>
                        <div className="ml-3">
                            <h3 className="text-sm font-medium text-gray-900">Success Rate</h3>
                            <p className="text-2xl font-semibold text-gray-700">
                                {stats?.jobs.success_rate.toFixed(1)}%
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {activeJobs && activeJobs.length > 0 && (
                <div className="mt-6">
                    <h3 className="text-sm font-medium text-gray-900">Active Scans</h3>
                    <div className="mt-2 space-y-2">
                        {activeJobs.map((job) => (
                            <div
                                key={job.id}
                                className="bg-gray-50 p-3 rounded-lg flex items-center justify-between"
                            >
                                <div>
                                    <p className="text-sm font-medium text-gray-900">{job.parameters.path}</p>
                                    <p className="text-xs text-gray-500">
                                        Started {formatDistanceToNow(new Date(job.start_time))} ago
                                    </p>
                                </div>
                                <div className="flex items-center">
                                    <LoadingSpinner size="sm" className="text-primary-500" />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}