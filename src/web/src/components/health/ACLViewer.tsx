import { useState } from 'react';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface ACLEntry {
    principal?: string;
    permissions?: string[];
    access_type?: string;
    inheritance?: string;
    description?: string;
    [key: string]: any;
}

interface ACLViewerProps {
    aclData: any;
    title: string;
}

export function ACLViewer({ aclData, title }: ACLViewerProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [showRawData, setShowRawData] = useState(false);

    if (!aclData || (typeof aclData === 'object' && Object.keys(aclData).length === 0)) {
        return null;
    }

    const handleToggleRaw = () => {
        setShowRawData(!showRawData);
        if (!isExpanded) {
            setIsExpanded(true);
        }
    };

    // Try to parse ACL data into a readable format
    const formatACLData = (data: any): ACLEntry[] => {
        // Handle string data (like recommendations)
        if (typeof data === 'string') {
            return [{
                description: data
            }];
        }
        
        if (Array.isArray(data)) {
            return data;
        }
        
        if (data && typeof data === 'object') {
            // Check for ACE array structures
            if (data.aces && Array.isArray(data.aces)) {
                return data.aces;
            }
            
            if (data.permissions && Array.isArray(data.permissions)) {
                return data.permissions;
            }
            
            // Check for direct_user_aces structure
            if (data.direct_user_aces && Array.isArray(data.direct_user_aces)) {
                return data.direct_user_aces;
            }
            
            // If it's an object with properties, try to extract meaningful information
            const entries: ACLEntry[] = [];
            for (const [key, value] of Object.entries(data)) {
                if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                    entries.push({
                        principal: key,
                        ...value as any
                    });
                } else if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
                    // Add simple key-value pairs as properties of a single entry
                    if (entries.length === 0) {
                        entries.push({});
                    }
                    entries[0][key] = value;
                }
            }
            return entries.length > 0 ? entries : [data];
        }
        
        return [{ description: String(data) }];
    };

    const aclEntries = formatACLData(aclData);

    return (
        <div className="border border-gray-200 rounded-lg bg-white shadow-sm">
            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-t-lg border-b border-gray-200">
                <h3 className="text-base font-bold text-gray-900 flex items-center">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mr-3"></span>
                    {title}
                </h3>
                <div className="flex items-center space-x-3">
                    <button
                        onClick={handleToggleRaw}
                        className="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-md transition-colors duration-200 bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                        {showRawData ? '📊 Show Formatted' : '🔧 Show Raw'}
                    </button>
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="flex items-center px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200 bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                        {isExpanded ? (
                            <>
                                <ChevronDownIcon className="h-4 w-4 mr-1" />
                                Hide
                            </>
                        ) : (
                            <>
                                <ChevronRightIcon className="h-4 w-4 mr-1" />
                                View
                            </>
                        )}
                    </button>
                </div>
            </div>
            
            {isExpanded && (
                <div className="p-4">
                    {showRawData ? (
                        <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                            <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap">
                                {JSON.stringify(aclData, null, 2)}
                            </pre>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {aclEntries.map((entry, index) => {
                                // Handle text-only entries (like recommendations)
                                if (entry.description && Object.keys(entry).length === 1) {
                                    return (
                                        <div key={index} className="bg-gradient-to-r from-amber-50 to-orange-50 p-4 rounded-lg border border-amber-200 shadow-sm">
                                            <div className="flex items-start">
                                                <span className="w-2 h-2 bg-amber-500 rounded-full mr-3 mt-2 flex-shrink-0"></span>
                                                <div className="text-gray-800 leading-relaxed">
                                                    {entry.description}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                }

                                // Handle ACE entries
                                return (
                                    <div key={index} className="bg-gradient-to-r from-gray-50 to-blue-50 p-4 rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200">
                                        <div className="flex items-center mb-3">
                                            <span className="w-1.5 h-6 bg-blue-500 rounded-full mr-3"></span>
                                            <h4 className="text-sm font-bold text-gray-800">
                                                {entry.principal ? `Principal: ${entry.principal}` : `Entry #${index + 1}`}
                                            </h4>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                            {entry.principal && (
                                                <div className="flex flex-col">
                                                    <span className="font-bold text-gray-800 text-xs uppercase tracking-wide mb-1">👤 Principal</span>
                                                    <span className="text-gray-700 bg-white px-3 py-2 rounded-md border font-medium">
                                                        {entry.principal}
                                                    </span>
                                                </div>
                                            )}
                                            {entry.access_type && (
                                                <div className="flex flex-col">
                                                    <span className="font-bold text-gray-800 text-xs uppercase tracking-wide mb-1">🔐 Access Type</span>
                                                    <span className={`px-3 py-2 rounded-md text-sm font-bold uppercase tracking-wide ${
                                                        entry.access_type.toLowerCase() === 'allow' 
                                                            ? 'bg-green-100 text-green-800 border border-green-200' 
                                                            : 'bg-red-100 text-red-800 border border-red-200'
                                                    }`}>
                                                        {entry.access_type.toLowerCase() === 'allow' ? '✅ ALLOW' : '❌ DENY'}
                                                    </span>
                                                </div>
                                            )}
                                            {entry.permissions && Array.isArray(entry.permissions) && (
                                                <div className="md:col-span-2">
                                                    <span className="font-bold text-gray-800 text-xs uppercase tracking-wide mb-2 block">🛡️ Permissions</span>
                                                    <div className="flex flex-wrap gap-2">
                                                        {entry.permissions.map((perm, permIndex) => (
                                                            <span 
                                                                key={permIndex}
                                                                className="px-3 py-1.5 bg-blue-100 text-blue-900 text-xs font-semibold rounded-full border border-blue-200 hover:bg-blue-200 transition-colors duration-150"
                                                            >
                                                                {perm}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                            {entry.inheritance && (
                                                <div className="flex flex-col">
                                                    <span className="font-bold text-gray-800 text-xs uppercase tracking-wide mb-1">🔗 Inheritance</span>
                                                    <span className="text-gray-700 bg-white px-3 py-2 rounded-md border">
                                                        {entry.inheritance}
                                                    </span>
                                                </div>
                                            )}
                                            {/* Display any other relevant fields */}
                                            {Object.entries(entry).map(([key, value]) => {
                                                if (['principal', 'permissions', 'access_type', 'inheritance', 'description'].includes(key)) {
                                                    return null;
                                                }
                                                if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
                                                    return (
                                                        <div key={key} className="flex flex-col">
                                                            <span className="font-bold text-gray-800 text-xs uppercase tracking-wide mb-1">
                                                                📋 {key.replace(/_/g, ' ').replace(/^\w/, c => c.toUpperCase())}
                                                            </span>
                                                            <span className="text-gray-700 bg-white px-3 py-2 rounded-md border">
                                                                {String(value)}
                                                            </span>
                                                        </div>
                                                    );
                                                }
                                                return null;
                                            })}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}