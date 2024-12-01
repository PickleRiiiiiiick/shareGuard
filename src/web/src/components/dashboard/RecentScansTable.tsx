import { useRecentScans } from '@/hooks/useScan';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { formatDistanceToNow } from 'date-fns';
import {
    CheckCircleIcon,
    XCircleIcon,
    ClockIcon
} from '@heroicons/react/24/outline';

const statusIcons = {
    completed: CheckCircleIcon,
    failed: XCircleIcon,
    running: ClockIcon,
} as const;

const statusColors = {
    completed: 'text-green-500',
    failed: 'text-red-500',
    running: 'text-primary-500',
} as const;

type ScanStatus = keyof typeof statusIcons;

export function RecentScansTable() {
    const { data: recentScans, isLoading } = useRecentScans(10);

    if (isLoading) {
        return (
            <div className="rounded-lg bg-white p-6 shadow">
                <div className="flex justify-center items-center h-48">
                    <LoadingSpinner />
                </div>
            </div>
        );
    }

    return (
        <div className="rounded-lg bg-white shadow">
            <div className="p-6">
                <h2 className="text-lg font-medium text-gray-900">Recent Scans</h2>
            </div>
            <div className="border-t border-gray-200">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Status
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Path
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Started
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Duration
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Initiated By
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {recentScans?.map((scan) => {
                                const status = scan.status as ScanStatus;
                                const StatusIcon = statusIcons[status];
                                const statusColor = statusColors[status];
                                const duration = scan.end_time
                                    ? formatDistanceToNow(new Date(scan.end_time), { addSuffix: true })
                                    : 'In Progress';

                                return (
                                    <tr key={scan.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <StatusIcon className={`h-5 w-5 ${statusColor}`} />
                                                <span className="ml-2 text-sm text-gray-500">
                                                    {status.charAt(0).toUpperCase() + status.slice(1)}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="text-sm text-gray-900">
                                                {scan.parameters.path}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="text-sm text-gray-500">
                                                {formatDistanceToNow(new Date(scan.start_time), { addSuffix: true })}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="text-sm text-gray-500">
                                                {duration}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {scan.created_by}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}