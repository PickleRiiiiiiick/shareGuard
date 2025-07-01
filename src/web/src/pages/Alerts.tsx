// src/web/src/pages/Alerts.tsx

import React, { useState } from 'react';
import AlertDashboard from '../components/alerts/AlertDashboard';
import AlertsList from '../components/alerts/AlertsList';
import AlertConfigurationManager from '../components/alerts/AlertConfigurationManager';
import NotificationCenter from '../components/alerts/NotificationCenter';
import { useAlertMutations, useMonitoringStatus } from '../hooks/useAlerts';
import { useAuth } from '../hooks/useAuth';

const Alerts: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'alerts' | 'configurations' | 'monitoring'>('dashboard');
  const { user } = useAuth();
  const { status } = useMonitoringStatus();
  const { startMonitoring, stopMonitoring } = useAlertMutations();

  const handleToggleMonitoring = async () => {
    try {
      if (status?.change_monitoring_active || status?.group_monitoring_active) {
        await stopMonitoring.mutateAsync();
      } else {
        await startMonitoring.mutateAsync();
      }
    } catch (error) {
      console.error('Failed to toggle monitoring:', error);
    }
  };

  const tabs = [
    {
      key: 'dashboard' as const,
      label: 'Dashboard',
      icon: '📊',
      description: 'Overview of alerts and monitoring status'
    },
    {
      key: 'alerts' as const,
      label: 'Alerts',
      icon: '🚨',
      description: 'View and manage active alerts'
    },
    {
      key: 'configurations' as const,
      label: 'Configurations',
      icon: '⚙️',
      description: 'Configure alert rules and conditions'
    },
    {
      key: 'monitoring' as const,
      label: 'Monitoring',
      icon: '👁️',
      description: 'Monitor real-time changes and group memberships'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">Security Alerts</h1>
              
              {/* Monitoring Status Indicator */}
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${
                  status?.change_monitoring_active || status?.group_monitoring_active ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <span className="text-sm text-gray-600">
                  Monitoring {status?.change_monitoring_active || status?.group_monitoring_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Monitoring Toggle */}
              <button
                onClick={handleToggleMonitoring}
                disabled={startMonitoring.isLoading || stopMonitoring.isLoading}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  status?.change_monitoring_active || status?.group_monitoring_active
                    ? 'bg-red-600 text-white hover:bg-red-700'
                    : 'bg-green-600 text-white hover:bg-green-700'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {startMonitoring.isLoading || stopMonitoring.isLoading
                  ? 'Processing...'
                  : status?.change_monitoring_active || status?.group_monitoring_active
                    ? 'Stop Monitoring'
                    : 'Start Monitoring'
                }
              </button>

              {/* Notification Center */}
              <NotificationCenter userId={user?.username} />
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </div>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <div className="space-y-8">
            <AlertDashboard />
            
            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
                <div className="space-y-3">
                  <button
                    onClick={() => setActiveTab('alerts')}
                    className="w-full text-left p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-xl">🚨</span>
                      <div>
                        <p className="font-medium text-gray-900">View Active Alerts</p>
                        <p className="text-sm text-gray-600">Review unacknowledged alerts</p>
                      </div>
                    </div>
                  </button>
                  
                  <button
                    onClick={() => setActiveTab('configurations')}
                    className="w-full text-left p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-xl">⚙️</span>
                      <div>
                        <p className="font-medium text-gray-900">Manage Alert Rules</p>
                        <p className="text-sm text-gray-600">Configure alert conditions</p>
                      </div>
                    </div>
                  </button>
                </div>
              </div>

              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Alerts</h3>
                <AlertsList showUnacknowledgedOnly={true} maxItems={5} />
              </div>

              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">System Status</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">ACL Monitoring</span>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${
                        status?.change_monitoring_active ? 'bg-green-500' : 'bg-red-500'
                      }`}></div>
                      <span className="text-sm font-medium">
                        {status?.change_monitoring_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Group Monitoring</span>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${
                        status?.group_monitoring_active ? 'bg-green-500' : 'bg-red-500'
                      }`}></div>
                      <span className="text-sm font-medium">
                        {status?.group_monitoring_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Connected Clients</span>
                    <span className="text-sm font-medium">
                      {status?.notification_service_stats?.active_connections || 0}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Groups Monitored</span>
                    <span className="text-sm font-medium">
                      {status?.group_monitoring_stats?.groups_monitored || 0}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'alerts' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900 mb-2">Security Alerts</h2>
                <p className="text-gray-600">
                  Review and manage security alerts generated by the monitoring system.
                  Acknowledge alerts once they have been reviewed and addressed.
                </p>
              </div>
              <AlertsList />
            </div>
          </div>
        )}

        {activeTab === 'configurations' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900 mb-2">Alert Configurations</h2>
                <p className="text-gray-600">
                  Define rules and conditions that determine when alerts are triggered.
                  Configure different alert types, severity levels, and notification preferences.
                </p>
              </div>
              <AlertConfigurationManager />
            </div>
          </div>
        )}

        {activeTab === 'monitoring' && (
          <div className="space-y-6">
            <MonitoringDetails status={status} />
          </div>
        )}
      </div>
    </div>
  );
};

// Monitoring Details Component
interface MonitoringDetailsProps {
  status: any;
}

const MonitoringDetails: React.FC<MonitoringDetailsProps> = ({ status }) => {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Monitoring Status</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* ACL Monitoring */}
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className={`w-4 h-4 rounded-full ${
                status?.change_monitoring_active ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <h3 className="text-lg font-medium text-gray-900">ACL Change Monitoring</h3>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Status:</span>
                <span className="text-sm font-medium">
                  {status?.change_monitoring_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              <div className="text-sm text-gray-600">
                <p>Monitors file system ACL changes in real-time using Windows APIs.</p>
                <p className="mt-2">Detects:</p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li>Permission additions and removals</li>
                  <li>Permission modifications</li>
                  <li>Inheritance changes</li>
                  <li>New file and folder access grants</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Group Monitoring */}
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className={`w-4 h-4 rounded-full ${
                status?.group_monitoring_active ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <h3 className="text-lg font-medium text-gray-900">Group Membership Monitoring</h3>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Status:</span>
                <span className="text-sm font-medium">
                  {status?.group_monitoring_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Groups Monitored:</span>
                <span className="text-sm font-medium">
                  {status?.group_monitoring_stats?.groups_monitored || 0}
                </span>
              </div>
              
              <div className="text-sm text-gray-600">
                <p>Tracks changes in group memberships that affect file access.</p>
                <p className="mt-2">Detects:</p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li>User additions to groups</li>
                  <li>User removals from groups</li>
                  <li>Nested group changes</li>
                  <li>Group access path modifications</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Notification Service Stats */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Notification Service</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {status?.notification_service_stats?.active_connections || 0}
            </div>
            <div className="text-sm text-gray-600">Active Connections</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {status?.notification_service_stats?.notifications_sent || 0}
            </div>
            <div className="text-sm text-gray-600">Notifications Sent</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {status?.notification_service_stats?.queue_size || 0}
            </div>
            <div className="text-sm text-gray-600">Queued</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {status?.notification_service_stats?.unique_users || 0}
            </div>
            <div className="text-sm text-gray-600">Connected Users</div>
          </div>
        </div>
      </div>

      {/* Configuration Details */}
      {status?.group_monitoring_stats?.configuration && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Monitoring Configuration</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">Snapshot Interval</div>
              <div className="text-lg font-medium">
                {Math.floor((status.group_monitoring_stats.configuration.snapshot_interval || 0) / 60)} minutes
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">Change Detection Interval</div>
              <div className="text-lg font-medium">
                {Math.floor((status.group_monitoring_stats.configuration.change_detection_interval || 0) / 60)} minutes
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">Snapshot Retention</div>
              <div className="text-lg font-medium">
                {Math.floor((status.group_monitoring_stats.configuration.max_snapshot_age || 0) / 86400)} days
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Alerts;