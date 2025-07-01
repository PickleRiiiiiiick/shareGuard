import { useState, useEffect, useCallback } from 'react';
import { ChevronUpIcon, ChevronDownIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { ACLIssue, IssueSeverity, IssueType, ISSUE_TYPE_LABELS, SEVERITY_COLORS, HealthPageSortConfig } from '../../types/health';

interface IssuesTableProps {
    issues: ACLIssue[];
    onIssueClick: (issue: ACLIssue) => void;
    sort: HealthPageSortConfig;
    onSortChange: (sort: HealthPageSortConfig) => void;
    onKeyboardNavigation?: (index: number) => void;
}

interface ColumnConfig {
    key: 'severity' | 'path' | 'type' | 'affectedPrincipals' | 'detectedAt';
    label: string;
    sortable: boolean;
    visible: boolean;
}

export function IssuesTable({ issues, onIssueClick, sort, onSortChange, onKeyboardNavigation }: IssuesTableProps) {
    const [columns, setColumns] = useState<ColumnConfig[]>([
        { key: 'severity', label: 'Severity', sortable: true, visible: true },
        { key: 'path', label: 'Path', sortable: true, visible: true },
        { key: 'type', label: 'Issue Type', sortable: true, visible: true },
        { key: 'affectedPrincipals', label: 'Users/Groups Involved', sortable: false, visible: true },
        { key: 'detectedAt', label: 'Detected At', sortable: true, visible: true },
    ]);
    const [showColumnMenu, setShowColumnMenu] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

    const handleSort = (field: 'severity' | 'path' | 'type' | 'detectedAt') => {
        if (sort.field === field) {
            onSortChange({
                field,
                direction: sort.direction === 'asc' ? 'desc' : 'asc',
            });
        } else {
            onSortChange({
                field,
                direction: 'desc',
            });
        }
    };

    const toggleColumn = (key: string) => {
        setColumns(columns.map(col => 
            col.key === key ? { ...col, visible: !col.visible } : col
        ));
    };

    const handleKeyDown = useCallback((e: KeyboardEvent) => {
        if (!issues.length) return;

        switch (e.key) {
            case 'ArrowUp':
                e.preventDefault();
                setSelectedIndex(prev => {
                    const newIndex = prev === null ? 0 : Math.max(0, prev - 1);
                    onKeyboardNavigation?.(newIndex);
                    return newIndex;
                });
                break;
            case 'ArrowDown':
                e.preventDefault();
                setSelectedIndex(prev => {
                    const newIndex = prev === null ? 0 : Math.min(issues.length - 1, prev + 1);
                    onKeyboardNavigation?.(newIndex);
                    return newIndex;
                });
                break;
            case 'Enter':
                e.preventDefault();
                if (selectedIndex !== null && issues[selectedIndex]) {
                    onIssueClick(issues[selectedIndex]);
                }
                break;
        }
    }, [issues, selectedIndex, onIssueClick, onKeyboardNavigation]);

    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [handleKeyDown]);

    const SortIcon = ({ field }: { field: 'severity' | 'path' | 'type' | 'detectedAt' }) => {
        if (sort.field !== field) {
            return <div className="w-4 h-4" />;
        }
        return sort.direction === 'asc' ? 
            <ChevronUpIcon className="w-4 h-4" /> : 
            <ChevronDownIcon className="w-4 h-4" />;
    };

    return (
        <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-3 border-b border-gray-200 flex justify-end">
                <div className="relative">
                    <button
                        onClick={() => setShowColumnMenu(!showColumnMenu)}
                        className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                        <EyeIcon className="h-4 w-4 mr-1" />
                        Columns
                    </button>
                    {showColumnMenu && (
                        <div className="absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-10">
                            <div className="py-1" role="menu">
                                {columns.map(column => (
                                    <button
                                        key={column.key}
                                        onClick={() => toggleColumn(column.key)}
                                        className="flex items-center justify-between w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                        role="menuitem"
                                    >
                                        <span>{column.label}</span>
                                        {column.visible ? (
                                            <EyeIcon className="h-4 w-4 text-gray-400" />
                                        ) : (
                                            <EyeSlashIcon className="h-4 w-4 text-gray-400" />
                                        )}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50 sticky top-0">
                        <tr>
                            {columns.filter(col => col.visible).map(column => (
                                <th
                                    key={column.key}
                                    scope="col"
                                    className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                                        column.sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                                    }`}
                                    onClick={() => column.sortable && column.key !== 'affectedPrincipals' && handleSort(column.key as any)}
                                    role={column.sortable ? 'button' : undefined}
                                    aria-label={column.sortable ? `Sort by ${column.label}` : undefined}
                                >
                                    <div className="flex items-center space-x-1">
                                        <span>{column.label}</span>
                                        {column.sortable && column.key !== 'affectedPrincipals' && (
                                            <SortIcon field={column.key as any} />
                                        )}
                                    </div>
                                </th>
                            ))}
                            <th scope="col" className="relative px-6 py-3">
                                <span className="sr-only">Actions</span>
                            </th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {issues.map((issue, index) => (
                            <tr
                                key={issue.id}
                                className={`hover:bg-gray-50 cursor-pointer ${
                                    selectedIndex === index ? 'bg-blue-50' : ''
                                }`}
                                onClick={() => onIssueClick(issue)}
                                role="button"
                                tabIndex={0}
                                aria-label={`View details for ${issue.type} issue at ${issue.path}`}
                            >
                                {columns.filter(col => col.visible).map(column => {
                                    switch (column.key) {
                                        case 'severity':
                                            return (
                                                <td key={column.key} className="px-6 py-4 whitespace-nowrap">
                                                    <span
                                                        className={`inline-flex items-center rounded-md px-2.5 py-0.5 text-sm font-medium ${
                                                            SEVERITY_COLORS[issue.severity].bg
                                                        } ${SEVERITY_COLORS[issue.severity].text}`}
                                                    >
                                                        {issue.severity.toUpperCase()}
                                                    </span>
                                                </td>
                                            );
                                        case 'path':
                                            return (
                                                <td key={column.key} className="px-6 py-4 text-sm text-gray-900">
                                                    <div className="max-w-xs truncate" title={issue.path}>
                                                        {issue.path}
                                                    </div>
                                                </td>
                                            );
                                        case 'type':
                                            return (
                                                <td key={column.key} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                    {ISSUE_TYPE_LABELS[issue.type]}
                                                </td>
                                            );
                                        case 'affectedPrincipals':
                                            return (
                                                <td key={column.key} className="px-6 py-4 text-sm text-gray-500">
                                                    <div className="max-w-xs truncate">
                                                        {issue.affectedPrincipals.join(', ')}
                                                    </div>
                                                </td>
                                            );
                                        case 'detectedAt':
                                            return (
                                                <td key={column.key} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {new Date(issue.detectedAt).toLocaleDateString()}
                                                </td>
                                            );
                                        default:
                                            return null;
                                    }
                                })}
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <button
                                        className="text-primary-600 hover:text-primary-900"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onIssueClick(issue);
                                        }}
                                    >
                                        View Details
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}