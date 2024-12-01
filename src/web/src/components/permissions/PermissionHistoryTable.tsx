import { useState } from 'react';
import { usePermissionHistory } from '@/hooks/usePermissionHistory';
import { format } from 'date-fns';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { PermissionHistoryFilters, ChangeType } from '@/types/history';

export function PermissionHistoryTable() {
    const [filters, setFilters] = useState<PermissionHistoryFilters>({});
    const { data: changes, isLoading } = usePermissionHistory(filters);

    const changeTypeColors: Record<ChangeType, string> = {
        added: 'text-green-600 bg-green-50',
        removed: 'text-red-600 bg-red-50',
        modified: 'text-yellow-600 bg-yellow-50',
    };

    return (
        <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-gray-900">Permission Changes History</h3>

                {/* Filters */}
                <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <div>
                        <label htmlFor="path" className="block text-sm font-medium text-gray-700">
                            Path Filter
                        </label>
                        <input
                            type="text"
                            id="path"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                            value={filters.path || ''}
                            onChange={(e) => setFilters(prev => ({ ...prev, path: e.target.value }))}
                        />
                    </div>

                    <div>
                        <label htmlFor="trustee" className="block text-sm font-medium text-gray-700">
                            Trustee
                        </label>
                        <input
                            type="text"
                            id="trustee"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                            value={filters.trustee || ''}
                            onChange={(e) => setFilters(prev => ({ ...prev, trustee: e.target.value }))}
                        />
                    </div>

                    <div>
                        <label htmlFor="changeType" className="block text-sm font-medium text-gray-700">
                            Change Type
                        </label>
                        <select
                            id="changeType"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                            value={filters.changeType || ''}
                            onChange={(e) =>
                                setFilters(prev => ({
                                    ...prev,
                                    changeType: e.target.value as ChangeType | undefined
                                }))
                            }
                        >
                            <option value="">All Changes</option>
                            <option value="added">Added</option>
                            <option value="removed">Removed</option>
                            <option value="modified">Modified</option>
                        </select>
                    </div>
                </div>

                {/* Table */}
                {isLoading ? (
                    <div className="mt-6 flex justify-center">
                        <LoadingSpinner />
                    </div>
                ) : (
                    <div className="mt-6 flow-root">
                        <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                            <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
                                <table className="min-w-full divide-y divide-gray-300">
                                    <thead>
                                        <tr>
                                            <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                                                Time
                                            </th>
                                            <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                                                Path
                                            </th>
                                            <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                                                Trustee
                                            </th>
                                            <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                                                Change Type
                                            </th>
                                            <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                                                Details
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-200">
                                        {changes?.map((change) => (
                                            <tr key={change.id}>
                                                <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                                                    {format(new Date(change.detected_time), 'PPp')}
                                                </td>
                                                <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                                                    {change.path}
                                                </td>
                                                <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                                                    {change.trustee_domain}\{change.trustee_name}
                                                </td>
                                                <td className="whitespace-nowrap px-3 py-4 text-sm">
                                                    <span
                                                        className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${changeTypeColors[change.change_type]}`}
                                                    >
                                                        {change.change_type}
                                                    </span>
                                                </td>
                                                <td className="px-3 py-4 text-sm text-gray-500">
                                                    <details className="cursor-pointer">
                                                        <summary>View changes</summary>
                                                        <div className="mt-2 text-xs">
                                                            <pre className="bg-gray-50 p-2 rounded">
                                                                {JSON.stringify(
                                                                    {
                                                                        previous: change.previous_state,
                                                                        current: change.current_state
                                                                    },
                                                                    null,
                                                                    2
                                                                )}
                                                            </pre>
                                                        </div>
                                                    </details>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
