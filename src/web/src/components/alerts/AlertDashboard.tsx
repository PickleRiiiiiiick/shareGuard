// src/web/src/components/alerts/AlertDashboard.tsx

import React, { useState } from 'react';
import { AlertSeverity, AlertType } from '../../types/alerts';
import { useAlertStatistics, useMonitoringStatus } from '../../hooks/useAlerts';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface AlertDashboardProps {
  className?: string;
}

const AlertDashboard: React.FC<AlertDashboardProps> = ({ className = '' }) => {
  const [timePeriod, setTimePeriod] = useState<number>(24);
  const { statistics, isLoading: statsLoading, error: statsError } = useAlertStatistics(timePeriod);
  const { status, isLoading: statusLoading, error: statusError } = useMonitoringStatus();

  if (statsLoading || statusLoading) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <LoadingSpinner />
      </div>
    );
  }

  if (statsError || statusError) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <h3 className="text-red-800 font-medium">Error Loading Dashboard</h3>
        <p className="text-red-600 text-sm mt-1">
          {statsError?.message || statusError?.message || 'Failed to load alert dashboard'}
        </p>
      </div>
    );
  }

  const getSeverityColor = (severity: AlertSeverity) => {
    switch (severity) {
      case AlertSeverity.CRITICAL:
        return 'bg-red-500 text-white';
      case AlertSeverity.HIGH:
        return 'bg-orange-500 text-white';
      case AlertSeverity.MEDIUM:
        return 'bg-yellow-500 text-white';
      case AlertSeverity.LOW:
        return 'bg-blue-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const getTypeIcon = (type: AlertType) => {
    switch (type) {
      case AlertType.PERMISSION_CHANGE:
        return '🔐';
      case AlertType.NEW_ACCESS:
        return '🔓';
      case AlertType.GROUP_MEMBERSHIP_CHANGE:
        return '👥';
      case AlertType.INHERITANCE_CHANGE:
        return '🔗';
      case AlertType.SENSITIVE_ACCESS:
        return '⚠️';
      default:
        return '📢';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Alert Dashboard</h2>
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">Time Period:</label>
          <select
            value={timePeriod}
            onChange={(e) => setTimePeriod(Number(e.target.value))}
            className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={1}>Last Hour</option>
            <option value={24}>Last 24 Hours</option>
            <option value={168}>Last Week</option>
            <option value={720}>Last Month</option>
          </select>
        </div>
      </div>

      {/* Monitoring Status */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Monitoring Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${status?.change_monitoring_active ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-600">ACL Monitoring</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${status?.group_monitoring_active ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-600">Group Monitoring</span>
          </div>
          <div className="flex items-center space-x-3">
            <span className="text-sm text-gray-600">Active Connections:</span>
            <span className="text-sm font-medium text-gray-900">
              {status?.notification_service_stats?.active_connections || 0}
            </span>
          </div>
          <div className="flex items-center space-x-3">
            <span className="text-sm text-gray-600">Groups Monitored:</span>
            <span className="text-sm font-medium text-gray-900">
              {status?.group_monitoring_stats?.groups_monitored || 0}
            </span>
          </div>
        </div>
      </div>

      {/* Alert Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Alerts</p>
              <p className="text-3xl font-bold text-gray-900">{statistics?.total_alerts || 0}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">📢</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Unacknowledged</p>
              <p className="text-3xl font-bold text-red-600">{statistics?.unacknowledged_alerts || 0}</p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">🚨</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Recent Changes</p>
              <p className="text-3xl font-bold text-green-600">{statistics?.recent_changes?.length || 0}</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">🔄</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Critical Alerts</p>
              <p className="text-3xl font-bold text-red-600">
                {statistics?.alerts_by_severity?.[AlertSeverity.CRITICAL] || 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">⚠️</span>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts by Severity */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Alerts by Severity</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(statistics?.alerts_by_severity || {}).map(([severity, count]) => (
            <div key={severity} className="text-center">
              <div className={`mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-2 ${getSeverityColor(severity as AlertSeverity)}`}>
                <span className="text-2xl font-bold">{count}</span>
              </div>
              <p className="text-sm font-medium text-gray-900 capitalize">{severity}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Alerts by Type */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Alerts by Type</h3>
        <div className="space-y-3">
          {Object.entries(statistics?.alerts_by_type || {}).map(([type, count]) => (
            <div key={type} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <span className="text-xl">{getTypeIcon(type as AlertType)}</span>
                <span className="text-sm font-medium text-gray-900 capitalize">
                  {type.replace(/_/g, ' ')}
                </span>
              </div>
              <span className="text-lg font-bold text-gray-700">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Changes */}
      {statistics?.recent_changes && statistics.recent_changes.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Changes</h3>
          <div className="space-y-3">
            {statistics.recent_changes.slice(0, 5).map((change) => (
              <div key={change.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="flex-shrink-0">
                  <span className="text-lg">
                    {change.change_type.includes('added') ? '➕' :
                     change.change_type.includes('removed') ? '➖' : '🔄'}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 capitalize">
                    {change.change_type.replace(/_/g, ' ')}
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(change.detected_time).toLocaleString()}
                  </p>
                  {change.current_state?.path && (
                    <p className="text-xs text-gray-600 truncate">
                      Path: {change.current_state.path}
                    </p>
                  )}
                  {change.current_state?.trustee && (
                    <p className="text-xs text-gray-600 truncate">
                      User: {change.current_state.trustee}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertDashboard;