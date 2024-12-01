import { useMemo } from 'react';

interface PermissionBadgeProps {
    permission: string;
    size?: 'sm' | 'md';
    className?: string;
}

export function PermissionBadge({
    permission,
    size = 'md',
    className = ''
}: PermissionBadgeProps) {
    const colorClass = useMemo(() => {
        switch (permission.toLowerCase()) {
            case 'full control':
                return 'bg-red-50 text-red-700 border-red-200';
            case 'modify':
                return 'bg-yellow-50 text-yellow-700 border-yellow-200';
            case 'write':
                return 'bg-orange-50 text-orange-700 border-orange-200';
            case 'read':
                return 'bg-green-50 text-green-700 border-green-200';
            case 'read & execute':
                return 'bg-blue-50 text-blue-700 border-blue-200';
            default:
                return 'bg-gray-50 text-gray-700 border-gray-200';
        }
    }, [permission]);

    const sizeClass = size === 'sm'
        ? 'px-2 py-0.5 text-xs'
        : 'px-2.5 py-1 text-sm';

    return (
        <span
            className={`inline-flex items-center rounded-md border ${sizeClass} font-medium ${colorClass} ${className}`}
        >
            {permission}
        </span>
    );
}