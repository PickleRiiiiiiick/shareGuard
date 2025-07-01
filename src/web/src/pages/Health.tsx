import { useState, useEffect } from 'react';
import { PlayIcon, ArrowDownTrayIcon, FunnelIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { useHealthScore, useIssues, useRunHealthScan, useExportIssues } from '../hooks/useHealth';
import { ScoreCard } from '../components/health/ScoreCard';
import { IssuesTable } from '../components/health/IssuesTable';
import { IssueDrawer } from '../components/health/IssueDrawer';
import { useAlert } from '../contexts/AlertContext';
import { useDebounce } from '../hooks/useDebounce';
import { ISSUE_TYPE_LABELS } from '../types/health';
import type { ACLIssue, HealthPageFilters, HealthPageSortConfig, IssueSeverity, IssueType } from '../types/health';

export function Health() {
    const [selectedIssue, setSelectedIssue] = useState<ACLIssue | null>(null);
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);
    const [currentPage, setCurrentPage] = useState(0);
    const [pageSize] = useState(50);
    const [showFilters, setShowFilters] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const debouncedSearchQuery = useDebounce(searchQuery, 300);
    
    const [filters, setFilters] = useState<HealthPageFilters>({
        severity: [],
        issueType: [],
        pathSubstring: '',
    });

    const [sort, setSort] = useState<HealthPageSortConfig>({
        field: 'severity',
        direction: 'desc',
    });

    const alert = useAlert();
    const { data: healthScore, isLoading: isScoreLoading } = useHealthScore();
    const { data: issuesData, isLoading: isIssuesLoading, refetch: refetchIssues } = useIssues({
        page: currentPage,
        pageSize,
        filters: { ...filters, searchQuery: debouncedSearchQuery },
        sort,
    });
    const runHealthScan = useRunHealthScan();
    const exportIssues = useExportIssues();

    const handleRunScan = async () => {
        try {
            await runHealthScan.mutateAsync();
            alert.success('Health scan started successfully');
        } catch (error) {
            alert.error('Failed to start health scan');
        }
    };

    const handleExport = async (format: 'csv' | 'pdf') => {
        try {
            if (format === 'pdf') {
                alert.warning('PDF export is not yet supported. Please use CSV format.');
                return;
            }
            // Only pass filters if they have actual values
            const cleanFilters = {
                severity: filters.severity?.length ? filters.severity : undefined,
                issueType: filters.issueType?.length ? filters.issueType : undefined,
                pathSubstring: filters.pathSubstring?.trim() || undefined,
            };
            await exportIssues.mutateAsync({ format, filters: cleanFilters });
            alert.success(`Issues exported as ${format.toUpperCase()}`);
        } catch (error) {
            alert.error(`Failed to export issues as ${format}`);
        }
    };

    const handleIssueClick = (issue: ACLIssue) => {
        setSelectedIssue(issue);
        setIsDrawerOpen(true);
    };

    const handleCloseDrawer = () => {
        setIsDrawerOpen(false);
        setTimeout(() => setSelectedIssue(null), 300);
    };

    const toggleSeverityFilter = (severity: IssueSeverity) => {
        setFilters(prev => ({
            ...prev,
            severity: prev.severity?.includes(severity)
                ? prev.severity.filter(s => s !== severity)
                : [...(prev.severity || []), severity],
        }));
        setCurrentPage(0);
    };

    const toggleIssueTypeFilter = (type: IssueType) => {
        setFilters(prev => ({
            ...prev,
            issueType: prev.issueType?.includes(type)
                ? prev.issueType.filter(t => t !== type)
                : [...(prev.issueType || []), type],
        }));
        setCurrentPage(0);
    };

    const totalPages = issuesData ? Math.ceil(issuesData.total / pageSize) : 0;

    if (isScoreLoading || !healthScore) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
        );
    }

    // Check if health score has an error
    const hasHealthError = healthScore && 'error' in healthScore;
    const hasIssuesError = issuesData && 'error' in issuesData;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">ACL Health Dashboard</h1>
                    <p className="text-gray-600 mt-1">Monitor your file system security and access control issues</p>
                </div>
                <button
                    onClick={handleRunScan}
                    disabled={runHealthScan.isPending}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
                >
                    <PlayIcon className="mr-2 h-4 w-4" />
                    {runHealthScan.isPending ? (
                        <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Running...
                        </>
                    ) : 'Run New Scan'}
                </button>
            </div>

            <div className="mb-6">
                {hasHealthError ? (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <div className="flex">
                            <div className="flex-shrink-0">
                                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                            </div>
                            <div className="ml-3">
                                <h3 className="text-sm font-medium text-yellow-800">
                                    Health Data Unavailable
                                </h3>
                                <div className="mt-2 text-sm text-yellow-700">
                                    <p>{(healthScore as any).error || 'Unable to load health score data. The database may not be initialized yet.'}</p>
                                    {(healthScore as any).message && <p className="mt-1">{(healthScore as any).message}</p>}
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <ScoreCard data={healthScore} />
                )}
            </div>

            <div className="bg-white shadow rounded-lg">
                <div className="px-4 py-3 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <div className="relative">
                                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Search issues..."
                                    value={searchQuery}
                                    onChange={(e) => {
                                        setSearchQuery(e.target.value);
                                        setCurrentPage(0);
                                    }}
                                    className="pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                />
                            </div>
                            <button
                                onClick={() => setShowFilters(!showFilters)}
                                className={`inline-flex items-center px-3 py-2 border shadow-sm text-sm font-medium rounded-md ${
                                    showFilters 
                                        ? 'border-blue-300 text-blue-700 bg-blue-50 hover:bg-blue-100' 
                                        : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
                                }`}
                            >
                                <FunnelIcon className="mr-2 h-4 w-4" />
                                Filters
                                {(filters.severity?.length || 0) + (filters.issueType?.length || 0) > 0 && (
                                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                        {(filters.severity?.length || 0) + (filters.issueType?.length || 0)}
                                    </span>
                                )}
                            </button>
                        </div>
                        <div className="flex items-center space-x-2">
                            <button
                                onClick={() => handleExport('csv')}
                                disabled={exportIssues.isPending}
                                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                            >
                                <ArrowDownTrayIcon className="mr-2 h-4 w-4" />
                                Export CSV
                            </button>
                            <button
                                onClick={() => handleExport('pdf')}
                                disabled={exportIssues.isPending}
                                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                            >
                                <ArrowDownTrayIcon className="mr-2 h-4 w-4" />
                                Export PDF
                            </button>
                        </div>
                    </div>
                </div>

                {showFilters && (
                    <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <h3 className="text-sm font-medium text-gray-900 mb-2">Severity</h3>
                                <div className="flex flex-wrap gap-2">
                                    {(['critical', 'high', 'medium', 'low'] as IssueSeverity[]).map(severity => (
                                        <button
                                            key={severity}
                                            onClick={() => toggleSeverityFilter(severity)}
                                            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                                                filters.severity?.includes(severity)
                                                    ? 'bg-blue-100 text-blue-800'
                                                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                            }`}
                                        >
                                            {severity.charAt(0).toUpperCase() + severity.slice(1)}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <h3 className="text-sm font-medium text-gray-900 mb-2">Issue Type</h3>
                                <div className="flex flex-wrap gap-2">
                                    {(Object.keys(ISSUE_TYPE_LABELS) as IssueType[]).map(type => (
                                        <button
                                            key={type}
                                            onClick={() => toggleIssueTypeFilter(type)}
                                            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                                                filters.issueType?.includes(type)
                                                    ? 'bg-blue-100 text-blue-800'
                                                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                            }`}
                                        >
                                            {ISSUE_TYPE_LABELS[type]}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <div className="mt-4">
                            <label htmlFor="path-filter" className="block text-sm font-medium text-gray-900 mb-1">
                                Path Filter
                            </label>
                            <input
                                id="path-filter"
                                type="text"
                                placeholder="Filter by path..."
                                value={filters.pathSubstring || ''}
                                onChange={(e) => {
                                    setFilters(prev => ({ ...prev, pathSubstring: e.target.value }));
                                    setCurrentPage(0);
                                }}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>
                    </div>
                )}

                {isIssuesLoading ? (
                    <div className="flex items-center justify-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                ) : hasIssuesError ? (
                    <div className="p-6">
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                            <div className="flex">
                                <div className="flex-shrink-0">
                                    <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                    </svg>
                                </div>
                                <div className="ml-3">
                                    <h3 className="text-sm font-medium text-yellow-800">
                                        Issues Data Unavailable
                                    </h3>
                                    <div className="mt-2 text-sm text-yellow-700">
                                        <p>{(issuesData as any).error || 'Unable to load issues data. The database may not be initialized yet.'}</p>
                                        <p className="mt-2">Try running a health scan to initialize the health data.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <>
                        <IssuesTable
                            issues={issuesData?.issues || []}
                            onIssueClick={handleIssueClick}
                            sort={sort}
                            onSortChange={setSort}
                        />
                        {totalPages > 1 && (
                            <div className="px-4 py-3 flex items-center justify-between border-t border-gray-200">
                                <div className="flex-1 flex justify-between sm:hidden">
                                    <button
                                        onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                                        disabled={currentPage === 0}
                                        className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                                    >
                                        Previous
                                    </button>
                                    <button
                                        onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                                        disabled={currentPage === totalPages - 1}
                                        className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                                    >
                                        Next
                                    </button>
                                </div>
                                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                                    <div>
                                        <p className="text-sm text-gray-700">
                                            Showing{' '}
                                            <span className="font-medium">{currentPage * pageSize + 1}</span> to{' '}
                                            <span className="font-medium">
                                                {Math.min((currentPage + 1) * pageSize, issuesData?.total || 0)}
                                            </span>{' '}
                                            of <span className="font-medium">{issuesData?.total || 0}</span> results
                                        </p>
                                    </div>
                                    <div>
                                        <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                                            <button
                                                onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                                                disabled={currentPage === 0}
                                                className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                                            >
                                                Previous
                                            </button>
                                            <button
                                                onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                                                disabled={currentPage === totalPages - 1}
                                                className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                                            >
                                                Next
                                            </button>
                                        </nav>
                                    </div>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>

            <IssueDrawer
                issue={selectedIssue}
                isOpen={isDrawerOpen}
                onClose={handleCloseDrawer}
            />
        </div>
    );
}