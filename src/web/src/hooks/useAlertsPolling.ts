// Alternative polling-based alerts hook
import { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { alertsApi } from '@/api/alerts';
import { useAlertContext } from '@/contexts/AlertContext';
import type { Alert } from '@/types/alerts';

interface AlertNotification {
  id: string;
  type: string;
  title: string;
  message: string;
  severity: string;
  timestamp: string;
  data?: any;
  read?: boolean;
}

export function useAlertsPolling(enabled: boolean = true) {
  const [notifications, setNotifications] = useState<AlertNotification[]>([]);
  const [lastAlertId, setLastAlertId] = useState<number | null>(null);
  const alertContext = useAlertContext();

  // Poll for new alerts every 5 seconds
  const { data: alerts, isLoading } = useQuery({
    queryKey: ['alerts', 'polling'],
    queryFn: () => alertsApi.getAlerts({
      acknowledged: false,
      hours: 1,
      limit: 50
    }),
    refetchInterval: enabled ? 5000 : false, // Poll every 5 seconds
    enabled
  });

  // Convert alerts to notifications and check for new ones
  useEffect(() => {
    if (!alerts?.length) return;

    const latestAlert = alerts[0];
    
    // Check if we have a new alert
    if (lastAlertId === null) {
      // First load - just set the latest ID without notifications
      setLastAlertId(latestAlert.id);
      return;
    }

    if (latestAlert.id > lastAlertId) {
      // We have new alerts
      const newAlerts = alerts.filter(alert => alert.id > lastAlertId);
      
      // Convert to notifications
      const newNotifications = newAlerts.map(alert => ({
        id: `alert-${alert.id}`,
        type: 'alert_triggered',
        title: `Alert: ${alert.severity.toUpperCase()}`,
        message: alert.message,
        severity: alert.severity,
        timestamp: alert.created_at,
        data: {
          alert_id: alert.id,
          config_id: alert.config_id,
          severity: alert.severity,
          details: alert.details
        },
        read: false
      }));

      // Add to notifications list
      setNotifications(prev => [...newNotifications, ...prev.slice(0, 99)]);

      // Show toast notifications
      newNotifications.forEach(notification => {
        if (notification.severity === 'critical') {
          alertContext.error(notification.message);
        } else if (notification.severity === 'high') {
          alertContext.warning(notification.message);
        } else {
          alertContext.info(notification.message);
        }
      });

      // Update last alert ID
      setLastAlertId(latestAlert.id);
    }
  }, [alerts, lastAlertId, alertContext]);

  const acknowledgeNotification = useCallback((notificationId: string) => {
    setNotifications(prev =>
      prev.map(notif =>
        notif.id === notificationId ? { ...notif, read: true } : notif
      )
    );
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // Get notification statistics
  const notificationStats = {
    total: notifications.length,
    unread: notifications.filter(n => !n.read).length,
    critical: notifications.filter(n => n.severity === 'critical').length,
    high: notifications.filter(n => n.severity === 'high').length
  };

  return {
    notifications,
    isLoading,
    connectionStatus: enabled ? 'connected' : 'disconnected',
    stats: notificationStats,
    acknowledgeNotification,
    clearNotifications,
    // WebSocket compatibility methods
    connect: () => {},
    disconnect: () => {},
    sendMessage: () => {},
    ping: () => {},
    updateFilters: () => {}
  };
}