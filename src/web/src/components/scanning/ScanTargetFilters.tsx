import { TargetFilters } from '@/types/target';
import { ScanScheduleType } from '@/types/enums';
import { debounce } from 'lodash';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';

interface ScanTargetFiltersProps {
    filters: TargetFilters;
    onChange: (filters: TargetFilters) => void;
}

export function ScanTargetFilters({ filters, onChange }: ScanTargetFiltersProps) {
    const handleSearchChange = debounce((search: string) => {
        onChange({ ...filters, search });
    }, 300);

    return (
        <div className="bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-4">
                <div>
                    <label htmlFor="search" className="block text-sm font-medium text-gray-700">
                        Search
                    </label>
                    <div className="mt-1 relative rounded-md shadow-sm">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                            type="text"
                            name="search"
                            id="search"
                            className="focus:ring-primary-500 focus:border-primary-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md"
                            placeholder="Search targets..."
                            onChange={(e) => handleSearchChange(e.target.value)}
                        />
                    </div>
                </div>

                <div>
                    <label htmlFor="department" className="block text-sm font-medium text-gray-700">
                        Department
                    </label>
                    <select
                        id="department"
                        name="department"
                        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                        value={filters.department || ''}
                        onChange={(e) => onChange({ ...filters, department: e.target.value || undefined })}
                    >
                        <option value="">All Departments</option>
                        <option value="it">IT</option>
                        <option value="hr">HR</option>
                        <option value="finance">Finance</option>
                    </select>
                </div>

                <div>
                    <label htmlFor="frequency" className="block text-sm font-medium text-gray-700">
                        Scan Frequency
                    </label>
                    <select
                        id="frequency"
                        name="frequency"
                        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                        value={filters.frequency || ''}
                        onChange={(e) => onChange({ ...filters, frequency: e.target.value as ScanScheduleType || undefined })}
                    >
                        <option value="">All Frequencies</option>
                        {Object.values(ScanScheduleType).map((frequency) => (
                            <option key={frequency} value={frequency}>
                                {frequency.charAt(0).toUpperCase() + frequency.slice(1)}
                            </option>
                        ))}
                    </select>
                </div>

                <div>
                    <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                        Status
                    </label>
                    <select
                        id="status"
                        name="status"
                        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                        value={filters.status || ''}
                        onChange={(e) => onChange({ ...filters, status: e.target.value as 'active' | 'disabled' || undefined })}
                    >
                        <option value="">All Status</option>
                        <option value="active">Active</option>
                        <option value="disabled">Disabled</option>
                    </select>
                </div>
            </div>
        </div>
    );
}