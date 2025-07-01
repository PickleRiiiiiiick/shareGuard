// 📄 File: /src/components/scanning/ScanResultsViewer.tsx

import React from 'react';
import { useScanResults } from '@/hooks/useScanResults';
import { format } from 'date-fns';

interface Props {
    targetId: number;
}

export const ScanResultsViewer: React.FC<Props> = ({ targetId }) => {
    const { data, isLoading, isError, error } = useScanResults(targetId);

    if (isLoading) {
        return <p className="text-sm text-gray-500 mt-2">Loading scan results...</p>;
    }

    if (isError) {
        return (
            <p className="text-sm text-red-600 mt-2">
                Failed to load scan results: {error instanceof Error ? error.message : 'Unknown error'}
            </p>
        );
    }

    if (!data || data.length === 0) {
        return <p className="text-sm text-gray-500 mt-2">No scan results available for this target.</p>;
    }

    return (
        <div className="mt-4 overflow-x-auto border border-gray-200 rounded-lg">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-4 py-2 text-left font-semibold text-gray-600">Path</th>
                        <th className="px-4 py-2 text-left font-semibold text-gray-600">Status</th>
                        <th className="px-4 py-2 text-left font-semibold text-gray-600">Permissions</th>
                        <th className="px-4 py-2 text-left font-semibold text-gray-600">Detected At</th>
                        <th className="px-4 py-2 text-left font-semibold text-gray-600">Issue</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                    {data.map((result, index) => (
                        <tr key={index}>
                            <td className="px-4 py-2 text-gray-900">{result.path}</td>
                            <td className="px-4 py-2">{result.status}</td>
                            <td className="px-4 py-2">
                                {result.permissions && result.permissions.length > 0
                                    ? result.permissions.join(', ')
                                    : 'None'}
                            </td>
                            <td className="px-4 py-2 text-gray-500">
                                {format(new Date(result.detected_at), 'PPPpp')}
                            </td>
                            <td className="px-4 py-2 text-gray-700">{result.issue_summary || '—'}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};
