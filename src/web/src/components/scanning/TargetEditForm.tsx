import { useState } from 'react';
import { ScanTarget } from '@/types/target';
import { ScanScheduleType } from '@/types/enums';

interface TargetEditFormProps {
    target: ScanTarget;
    onSubmit: (data: Partial<ScanTarget>) => void;
    onCancel: () => void;
    isLoading: boolean;
}

export function TargetEditForm({ target, onSubmit, onCancel, isLoading }: TargetEditFormProps) {
    const [formData, setFormData] = useState<Partial<ScanTarget>>({
        name: target.name,
        path: target.path,
        description: target.description,
        department: target.department,
        owner: target.owner,
        sensitivity_level: target.sensitivity_level,
        is_sensitive: target.is_sensitive,
        scan_frequency: target.scan_frequency,
        max_depth: target.max_depth,
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit(formData);
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            <div>
                <h3 className="text-lg font-medium text-gray-900">Edit Target</h3>
                <div className="mt-6 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
                    <div>
                        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                            Name
                        </label>
                        <input
                            type="text"
                            name="name"
                            id="name"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                            required
                        />
                    </div>

                    <div>
                        <label htmlFor="path" className="block text-sm font-medium text-gray-700">
                            Path
                        </label>
                        <input
                            type="text"
                            name="path"
                            id="path"
                            value={formData.path}
                            onChange={(e) => setFormData({ ...formData, path: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                            required
                        />
                    </div>

                    <div>
                        <label htmlFor="department" className="block text-sm font-medium text-gray-700">
                            Department
                        </label>
                        <input
                            type="text"
                            name="department"
                            id="department"
                            value={formData.department || ''}
                            onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        />
                    </div>

                    <div>
                        <label htmlFor="owner" className="block text-sm font-medium text-gray-700">
                            Owner
                        </label>
                        <input
                            type="text"
                            name="owner"
                            id="owner"
                            value={formData.owner || ''}
                            onChange={(e) => setFormData({ ...formData, owner: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        />
                    </div>

                    <div>
                        <label htmlFor="scan_frequency" className="block text-sm font-medium text-gray-700">
                            Monitoring Status & Scan Frequency
                        </label>
                        <select
                            id="scan_frequency"
                            name="scan_frequency"
                            value={formData.scan_frequency}
                            onChange={(e) => setFormData({ ...formData, scan_frequency: e.target.value as ScanScheduleType })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        >
                            <option value="disabled">🔴 Inactive (Disabled)</option>
                            {Object.values(ScanScheduleType).filter(f => f !== 'disabled').map((frequency) => (
                                <option key={frequency} value={frequency}>
                                    🟢 Active - {frequency.charAt(0).toUpperCase() + frequency.slice(1)}
                                </option>
                            ))}
                        </select>
                        <p className="mt-1 text-xs text-gray-500">
                            Only active targets are monitored for ACL changes
                        </p>
                    </div>

                    <div>
                        <label htmlFor="max_depth" className="block text-sm font-medium text-gray-700">
                            Max Depth
                        </label>
                        <input
                            type="number"
                            name="max_depth"
                            id="max_depth"
                            value={formData.max_depth || ''}
                            onChange={(e) => setFormData({ ...formData, max_depth: parseInt(e.target.value) })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        />
                    </div>

                    <div className="sm:col-span-2">
                        <div className="flex items-center">
                            <input
                                id="is_sensitive"
                                name="is_sensitive"
                                type="checkbox"
                                checked={formData.is_sensitive}
                                onChange={(e) => setFormData({ ...formData, is_sensitive: e.target.checked })}
                                className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                            />
                            <label htmlFor="is_sensitive" className="ml-2 block text-sm text-gray-700">
                                Mark as sensitive target
                            </label>
                        </div>
                    </div>

                    <div className="sm:col-span-2">
                        <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                            Description
                        </label>
                        <textarea
                            id="description"
                            name="description"
                            rows={3}
                            value={formData.description || ''}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        />
                    </div>
                </div>
            </div>

            <div className="flex justify-end space-x-3">
                <button
                    type="button"
                    onClick={onCancel}
                    className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    disabled={isLoading}
                    className="inline-flex justify-center rounded-md border border-transparent bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                >
                    {isLoading ? 'Saving...' : 'Save Changes'}
                </button>
            </div>
        </form>
    );
}