// src/web/src/components/alerts/NotificationCenter.tsx

import React, { useState, useEffect } from 'react';
import { WebSocketNotification, WebSocketFilters } from '../../types/alerts';
import { useWebSocketNotifications } from '../../hooks/useAlerts';

interface NotificationCenterProps {
  className?: string;
  userId?: string;
  initialFilters?: WebSocketFilters;
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({
  className = '',
  userId,
  initialFilters
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [filters, setFilters] = useState<WebSocketFilters>(initialFilters || {});
  
  const {
    notifications,
    connectionStatus,
    updateFilters,
    acknowledgeNotification,
    clearNotifications,
    unreadCount
  } = useWebSocketNotifications(userId, filters);

  useEffect(() => {
    if (filters !== initialFilters) {
      updateFilters(filters);
    }
  }, [filters, updateFilters, initialFilters]);

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-500';
      case 'connecting': return 'bg-yellow-500';
      case 'disconnected': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'permission_change': return '🔐';
      case 'group_membership_change': return '👥';
      case 'new_access_granted': return '🔓';
      case 'access_removed': return '🚫';
      case 'alert_triggered': return '🚨';
      case 'system_status': return '⚙️';
      default: return '📢';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'border-l-red-500 bg-red-50';
      case 'high': return 'border-l-orange-500 bg-orange-50';
      case 'medium': return 'border-l-yellow-500 bg-yellow-50';
      case 'low': return 'border-l-blue-500 bg-blue-50';
      default: return 'border-l-gray-500 bg-gray-50';
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
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

  return (
    <div className={`relative ${className}`}>
      {/* Notification Bell Icon */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-400 hover:text-gray-600 transition-colors"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        
        {/* Unread Count Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
        
        {/* Connection Status Indicator */}
        <div className={`absolute top-0 right-0 w-3 h-3 rounded-full ${getConnectionStatusColor()}`}></div>
      </button>

      {/* Notification Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-medium text-gray-900">Notifications</h3>
              <div className={`w-2 h-2 rounded-full ${getConnectionStatusColor()}`}></div>
              <span className="text-xs text-gray-500 capitalize">{connectionStatus}</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={clearNotifications}
                className="text-xs text-gray-500 hover:text-gray-700"
                title="Clear all"
              >
                Clear All
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Filters */}
          <div className="p-3 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center space-x-2">
              <label className="text-xs text-gray-600">Min Severity:</label>
              <select
                value={filters.min_severity || ''}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  min_severity: e.target.value as any || undefined
                }))}
                className="text-xs border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">All</option>
                <option value="low">Low+</option>
                <option value="medium">Medium+</option>
                <option value="high">High+</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-8 text-center">
                <span className="text-4xl">🔕</span>
                <p className="text-sm text-gray-500 mt-2">No notifications</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {notifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onAcknowledge={() => acknowledgeNotification(notification.id)}
                    getNotificationIcon={getNotificationIcon}
                    getSeverityColor={getSeverityColor}
                    formatTimeAgo={formatTimeAgo}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-gray-200 bg-gray-50 text-center">
            <button
              onClick={() => {
                setIsOpen(false);
                // Navigate to full alerts page
                window.location.href = '/alerts';
              }}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              View All Alerts
            </button>
          </div>
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsOpen(false)}
        ></div>
      )}
    </div>
  );
};

// Notification Item Component
interface NotificationItemProps {
  notification: WebSocketNotification;
  onAcknowledge: () => void;
  getNotificationIcon: (type: string) => string;
  getSeverityColor: (severity: string) => string;
  formatTimeAgo: (timestamp: string) => string;
}

const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
  onAcknowledge,
  getNotificationIcon,
  getSeverityColor,
  formatTimeAgo
}) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className={`p-3 border-l-4 ${getSeverityColor(notification.severity)} ${
      notification.read ? 'opacity-60' : ''
    }`}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <span className="text-lg">{getNotificationIcon(notification.type)}</span>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <p className="text-sm font-medium text-gray-900 truncate">
              {notification.title}
            </p>
            <div className="flex items-center space-x-1">
              <span className="text-xs text-gray-500">
                {formatTimeAgo(notification.timestamp)}
              </span>
              {!notification.read && (
                <button
                  onClick={onAcknowledge}
                  className="text-xs text-blue-600 hover:text-blue-800"
                  title="Mark as read"
                >
                  ✓
                </button>
              )}
            </div>
          </div>
          
          <p className="text-sm text-gray-600 mb-2">{notification.message}</p>
          
          {/* Severity and Type badges */}
          <div className="flex items-center space-x-2 mb-2">
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
              notification.severity === 'critical' ? 'bg-red-100 text-red-800' :
              notification.severity === 'high' ? 'bg-orange-100 text-orange-800' :
              notification.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
              'bg-blue-100 text-blue-800'
            }`}>
              {notification.severity.toUpperCase()}
            </span>
            
            <span className="text-xs text-gray-500 capitalize">
              {notification.type.replace(/_/g, ' ')}
            </span>
          </div>

          {/* Toggle Details */}
          {notification.data && Object.keys(notification.data).length > 0 && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-xs text-gray-500 hover:text-gray-700 flex items-center"
            >
              <span className="mr-1">Details</span>
              <svg className={`w-3 h-3 transform transition-transform ${showDetails ? 'rotate-180' : ''}`} 
                   fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          )}

          {/* Details */}
          {showDetails && notification.data && (
            <div className="mt-2 p-2 bg-white rounded border">
              <pre className="text-xs text-gray-600 overflow-x-auto">
                {JSON.stringify(notification.data, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NotificationCenter;