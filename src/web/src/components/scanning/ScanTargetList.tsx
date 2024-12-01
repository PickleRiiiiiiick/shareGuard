import { useState } from 'react';
import { useTargets } from '@/hooks/useTargets';
import { LoadingSpinner } from '@components/common/LoadingSpinner';
import { TargetFilters } from '@/types/target';
import { ScanTargetRow } from './ScanTargetRow';
import { ScanTargetFilters } from './ScanTargetFilters';
import { NewTargetButton } from './NewTargetButton';

export function ScanTargetList() {
    const [filters, setFilters] = useState<TargetFilters>({});
    const { data: targets, isLoading } = useTargets(filters);

    return (
        <div className="space-y-6">
            <div className="sm:flex sm:items-center">
                <div className="sm:flex-auto">
                    <h1 className="text-2xl font-semibold text-gray-900">Scan Targets</h1>
                    <p className="mt-2 text-sm text-gray-700">
                        A list of all scan targets including their paths, schedules, and last scan status.
                    </p>
                </div>
                <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
                    <NewTargetButton />
                </div>
            </div>

            <ScanTargetFilters filters={filters} onChange={setFilters} />

            {isLoading ? (
                <div className="flex justify-center items-center h-64">
                    <LoadingSpinner />
                </div>
            ) : (
                <div className="overflow-hidden bg-white shadow sm:rounded-lg">
                    <ul role="list" className="divide-y divide-gray-200">
                        {targets?.map((target) => (
                            <ScanTargetRow key={target.id} target={target} />
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}