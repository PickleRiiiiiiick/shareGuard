// src/web/src/components/alerts/AlertsList.tsx

import React, { useState } from 'react';
import {
  Alert,
  AlertSeverity,
  AlertType,
  AlertsFilters,
  AlertAcknowledge
} from '../../types/alerts';
import { useAlerts, useAlertMutations } from '../../hooks/useAlerts';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface AlertsListProps {
  className?: string;
  showUnacknowledgedOnly?: boolean;
  maxItems?: number;
}

const AlertsList: React.FC<AlertsListProps> = ({
  className = '',
  showUnacknowledgedOnly = false,
  maxItems
}) => {
  const [filters, setFilters] = useState<AlertsFilters>({
    acknowledged: showUnacknowledgedOnly ? false : undefined,
    hours: 24,
    limit: maxItems || 50
  });
  const [acknowledgeForm, setAcknowledgeForm] = useState<{
    alertId: number;
    notes: string;
  } | null>(null);

  const { alerts, isLoading, error, refetch } = useAlerts(filters);
  const { acknowledgeAlert } = useAlertMutations();

  const handleAcknowledge = async (alertId: number, acknowledgment: AlertAcknowledge) => {
    try {
      await acknowledgeAlert.mutateAsync({ alertId, acknowledgment });
      setAcknowledgeForm(null);
      refetch();
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const getSeverityColor = (severity: AlertSeverity) => {
    switch (severity) {
      case AlertSeverity.CRITICAL:
        return 'bg-red-100 text-red-800 border-red-200';
      case AlertSeverity.HIGH:
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case AlertSeverity.MEDIUM:
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case AlertSeverity.LOW:
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getSeverityIcon = (severity: AlertSeverity) => {
    switch (severity) {
      case AlertSeverity.CRITICAL: return '🚨';
      case AlertSeverity.HIGH: return '⚠️';
      case AlertSeverity.MEDIUM: return '⚡';
      case AlertSeverity.LOW: return 'ℹ️';
      default: return '📢';
    }
  };

  const getTypeIcon = (type?: string) => {
    switch (type) {
      case AlertType.PERMISSION_CHANGE: return '🔐';
      case AlertType.NEW_ACCESS: return '🔓';
      case AlertType.GROUP_MEMBERSHIP_CHANGE: return '👥';
      case AlertType.INHERITANCE_CHANGE: return '🔗';
      case AlertType.SENSITIVE_ACCESS: return '⚠️';
      default: return '📢';
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  const isRecentAlert = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    return minutes < 10; // Alert is "recent" if less than 10 minutes old
  };

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <h3 className="text-red-800 font-medium">Error Loading Alerts</h3>
        <p className="text-red-600 text-sm mt-1">{error.message}</p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header and Filters */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">
          {showUnacknowledgedOnly ? 'Unacknowledged Alerts' : 'Recent Alerts'}
        </h2>
        
        {!showUnacknowledgedOnly && (
          <div className="flex items-center space-x-4">
            <select
              value={filters.severity || ''}
              onChange={(e) => setFilters(prev => ({
                ...prev,
                severity: e.target.value as AlertSeverity || undefined
              }))}
              className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Severities</option>
              {Object.values(AlertSeverity).map(severity => (
                <option key={severity} value={severity}>{severity.toUpperCase()}</option>
              ))}
            </select>

            <select
              value={filters.hours || 24}
              onChange={(e) => setFilters(prev => ({
                ...prev,
                hours: Number(e.target.value)
              }))}
              className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={1}>Last Hour</option>
              <option value={24}>Last 24 Hours</option>
              <option value={168}>Last Week</option>
              <option value={720}>Last Month</option>
            </select>

            <label className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={filters.acknowledged === false}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  acknowledged: e.target.checked ? false : undefined
                }))}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
              />
              Unacknowledged only
            </label>
          </div>
        )}
      </div>

      {/* Alerts List */}
      {alerts.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <span className="text-6xl">🔕</span>
          <h3 className="text-lg font-medium text-gray-900 mt-4">No Alerts</h3>
          <p className="text-gray-600 mt-2">
            {showUnacknowledgedOnly 
              ? 'All alerts have been acknowledged.' 
              : 'No alerts found for the selected criteria.'
            }
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={(acknowledgment) => handleAcknowledge(alert.id, acknowledgment)}
              getSeverityColor={getSeverityColor}
              getSeverityIcon={getSeverityIcon}
              getTypeIcon={getTypeIcon}
              formatTimeAgo={formatTimeAgo}
              isRecent={isRecentAlert(alert.created_at)}
            />
          ))}
        </div>
      )}

      {/* Acknowledge Modal */}
      {acknowledgeForm && (
        <AcknowledgeModal
          alertId={acknowledgeForm.alertId}
          notes={acknowledgeForm.notes}
          onNotesChange={(notes) => setAcknowledgeForm(prev => prev ? { ...prev, notes } : null)}
          onSave={(acknowledgment) => handleAcknowledge(acknowledgeForm.alertId, acknowledgment)}
          onCancel={() => setAcknowledgeForm(null)}
        />
      )}
    </div>
  );
};

// Helper function to render user-friendly alert details
const renderAlertDetails = (details: any) => {
  // Check if this is our new formatted structure
  if (details && details.folder && details.changes && details.metadata) {
    return (
      <div className="space-y-4">
        {/* Folder Information */}
        <div className="bg-blue-50 rounded-lg p-3">
          <h4 className="text-sm font-medium text-blue-900 mb-2">📁 Affected Folder</h4>
          <div className="text-sm text-blue-800">
            <p className="font-medium">{details.folder.name}</p>
            <p className="text-xs text-blue-600 mt-1">{details.folder.full_path}</p>
          </div>
        </div>

        {/* Summary */}
        <div className="bg-gray-50 rounded-lg p-3">
          <h4 className="text-sm font-medium text-gray-900 mb-2">📊 Summary</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Changes Detected:</span>
              <span className="ml-2 font-medium">{details.summary.changes_detected}</span>
            </div>
            <div>
              <span className="text-gray-600">Severity Level:</span>
              <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                details.summary.severity_level === 'high' ? 'bg-red-100 text-red-800' :
                details.summary.severity_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                'bg-blue-100 text-blue-800'
              }`}>
                {details.summary.severity_level.toUpperCase()}
              </span>
            </div>
          </div>
        </div>

        {/* Changes */}
        {details.changes && details.changes.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-3">🔍 Changes Detected</h4>
            <div className="space-y-3">
              {details.changes.map((change: any, index: number) => (
                <div key={index} className="border border-gray-200 rounded-lg p-3">
                  <div className="flex items-start space-x-3">
                    <span className="text-xl">{change.icon}</span>
                    <div className="flex-1">
                      <h5 className="text-sm font-medium text-gray-900">{change.type}</h5>
                      <p className="text-sm text-gray-700 mt-1">{change.description}</p>
                      
                      {change.users_affected && change.users_affected.length > 0 && (
                        <div className="mt-2">
                          <span className="text-xs font-medium text-gray-600">Users/Groups Affected:</span>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {change.users_affected.map((user: string, userIndex: number) => (
                              <span key={userIndex} className="inline-block bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded">
                                {user}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      <div className="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-600">
                        <strong>Impact:</strong> {change.impact}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Metadata */}
        <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600">
          <h4 className="text-sm font-medium text-gray-900 mb-2">ℹ️ Detection Information</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            <div>
              <span className="font-medium">Source:</span> {details.metadata.source}
            </div>
            <div>
              <span className="font-medium">Type:</span> {details.metadata.alert_type}
            </div>
            <div>
              <span className="font-medium">Detected:</span> {new Date(details.metadata.detected_at).toLocaleString()}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Fallback to old format for existing alerts
  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-gray-900">Details:</h4>
      <pre className="text-xs text-gray-600 bg-gray-50 p-2 rounded overflow-x-auto">
        {JSON.stringify(details, null, 2)}
      </pre>
    </div>
  );
};

// Alert Card Component
interface AlertCardProps {
  alert: Alert;
  onAcknowledge: (acknowledgment: AlertAcknowledge) => void;
  getSeverityColor: (severity: AlertSeverity) => string;
  getSeverityIcon: (severity: AlertSeverity) => string;
  getTypeIcon: (type?: string) => string;
  formatTimeAgo: (dateString: string) => string;
  isRecent: boolean;
}

const AlertCard: React.FC<AlertCardProps> = ({
  alert,
  onAcknowledge,
  getSeverityColor,
  getSeverityIcon,
  getTypeIcon,
  formatTimeAgo,
  isRecent
}) => {
  const [showDetails, setShowDetails] = useState(false);
  // const [showAcknowledgeForm, setShowAcknowledgeForm] = useState(false);

  const handleQuickAcknowledge = () => {
    onAcknowledge({
      acknowledged_by: 'current_user', // This should come from auth context
      notes: undefined
    });
  };

  return (
    <div className={`bg-white rounded-lg border-2 transition-all duration-200 relative ${
      alert.acknowledged_at ? 'border-gray-200 opacity-75' : getSeverityColor(alert.severity).replace('bg-', 'border-').replace('text-', '')
    } ${isRecent && !alert.acknowledged_at ? 'shadow-lg ring-2 ring-blue-500 ring-opacity-50' : ''}`}>
      {isRecent && !alert.acknowledged_at && (
        <div className="absolute -top-2 -right-2 bg-blue-500 text-white text-xs px-2 py-1 rounded-full font-medium animate-pulse">
          NEW
        </div>
      )}
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1">
            <div className="flex-shrink-0">
              <span className="text-2xl">{getSeverityIcon(alert.severity)}</span>
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(alert.severity)}`}>
                  {alert.severity.toUpperCase()}
                </span>
                {alert.configuration?.alert_type && (
                  <span className="text-xs text-gray-500 flex items-center">
                    <span className="mr-1">{getTypeIcon(alert.configuration.alert_type)}</span>
                    {alert.configuration.alert_type.replace(/_/g, ' ').toUpperCase()}
                  </span>
                )}
                <span className={`text-xs ${isRecent ? 'text-blue-600 font-medium' : 'text-gray-500'}`}>
                  {isRecent && '🔴 '}{formatTimeAgo(alert.created_at)}
                </span>
              </div>
              
              <p className="text-sm font-medium text-gray-900 mb-1">{alert.message}</p>
              
              {alert.configuration_name && (
                <p className="text-xs text-gray-600">Configuration: {alert.configuration_name}</p>
              )}
              
              {alert.target_name && (
                <p className="text-xs text-gray-600">Target: {alert.target_name}</p>
              )}
              
              {alert.acknowledged_at && (
                <div className="mt-2 flex items-center text-xs text-green-600">
                  <span className="mr-1">✓</span>
                  Acknowledged by {alert.acknowledged_by} at {new Date(alert.acknowledged_at).toLocaleString()}
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-2 ml-4">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              title="Toggle details"
            >
              <svg className={`w-4 h-4 transform transition-transform ${showDetails ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {!alert.acknowledged_at && (
              <button
                onClick={handleQuickAcknowledge}
                className="px-3 py-1 text-xs text-green-700 bg-green-100 rounded-md hover:bg-green-200 transition-colors"
                title="Quick acknowledge"
              >
                Acknowledge
              </button>
            )}
          </div>
        </div>

        {/* Details Section */}
        {showDetails && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            {alert.details && renderAlertDetails(alert.details)}
          </div>
        )}
      </div>
    </div>
  );
};

// Acknowledge Modal Component
interface AcknowledgeModalProps {
  alertId: number;
  notes: string;
  onNotesChange: (notes: string) => void;
  onSave: (acknowledgment: AlertAcknowledge) => void;
  onCancel: () => void;
}

const AcknowledgeModal: React.FC<AcknowledgeModalProps> = ({
  alertId: _alertId,
  notes,
  onNotesChange,
  onSave,
  onCancel
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      acknowledged_by: 'current_user', // This should come from auth context
      notes: notes.trim() || undefined
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Acknowledge Alert</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes (Optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => onNotesChange(e.target.value)}
              rows={3}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Add any notes about this acknowledgment..."
            />
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm text-white bg-green-600 rounded-md hover:bg-green-700"
            >
              Acknowledge
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AlertsList;