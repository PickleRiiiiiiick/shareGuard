// src/web/src/hooks/useAlerts.ts

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  AlertConfiguration,
  AlertConfigurationCreate,
  AlertConfigurationUpdate,
  AlertAcknowledge,
  AlertStatistics,
  PermissionChange,
  MonitoringStatus,
  AlertsFilters,
  RecentChangesFilters
} from '../types/alerts';
import { alertsApi } from '../api/alerts';
import { useAlert } from '../contexts/AlertContext';

export const useAlerts = (filters?: AlertsFilters) => {
  const {
    data: alerts,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['alerts', filters],
    queryFn: () => alertsApi.getAlerts(filters),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  return {
    alerts: alerts || [],
    isLoading,
    error,
    refetch
  };
};

export const useAlertDetail = (alertId: number) => {
  const {
    data: alert,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['alert', alertId],
    queryFn: () => alertsApi.getAlert(alertId),
    enabled: !!alertId,
  });

  return {
    alert,
    isLoading,
    error,
    refetch
  };
};

export const useAlertConfigurations = (params?: {
  target_id?: number;
  is_active?: boolean;
  skip?: number;
  limit?: number;
}) => {
  const {
    data: configurations,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['alert-configurations', params],
    queryFn: () => alertsApi.getConfigurations(params),
  });

  return {
    configurations: configurations || [],
    isLoading,
    error,
    refetch
  };
};

export const useAlertConfiguration = (configId: number) => {
  const {
    data: configuration,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['alert-configuration', configId],
    queryFn: () => alertsApi.getConfiguration(configId),
    enabled: !!configId,
  });

  return {
    configuration,
    isLoading,
    error,
    refetch
  };
};

export const useAlertStatistics = (hours: number = 24) => {
  const {
    data: statistics,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['alert-statistics', hours],
    queryFn: () => alertsApi.getStatistics(hours),
    refetchInterval: 60000, // Refetch every minute
  });

  return {
    statistics,
    isLoading,
    error,
    refetch
  };
};

export const useRecentChanges = (filters?: RecentChangesFilters) => {
  const {
    data: changes,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['recent-changes', filters],
    queryFn: () => alertsApi.getRecentChanges(filters),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  return {
    changes: changes || [],
    isLoading,
    error,
    refetch
  };
};

export const useMonitoringStatus = () => {
  const {
    data: status,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['monitoring-status'],
    queryFn: () => alertsApi.getMonitoringStatus(),
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  return {
    status,
    isLoading,
    error,
    refetch
  };
};

export const useAlertMutations = () => {
  const queryClient = useQueryClient();
  const alertContext = useAlert();

  const createConfiguration = useMutation({
    mutationFn: (config: AlertConfigurationCreate) => alertsApi.createConfiguration(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-configurations'] });
      alertContext.success('Alert configuration created successfully');
    },
    onError: (error: any) => {
      alertContext.error(`Failed to create alert configuration: ${error.message}`);
    },
  });

  const updateConfiguration = useMutation({
    mutationFn: ({ configId, update }: { configId: number; update: AlertConfigurationUpdate }) =>
      alertsApi.updateConfiguration(configId, update),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-configurations'] });
      queryClient.invalidateQueries({ queryKey: ['alert-configuration'] });
      alertContext.success('Alert configuration updated successfully');
    },
    onError: (error: any) => {
      alertContext.error(`Failed to update alert configuration: ${error.message}`);
    },
  });

  const deleteConfiguration = useMutation({
    mutationFn: (configId: number) => alertsApi.deleteConfiguration(configId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-configurations'] });
      alertContext.success('Alert configuration deleted successfully');
    },
    onError: (error: any) => {
      alertContext.error(`Failed to delete alert configuration: ${error.message}`);
    },
  });

  const acknowledgeAlert = useMutation({
    mutationFn: ({ alertId, acknowledgment }: { alertId: number; acknowledgment: AlertAcknowledge }) =>
      alertsApi.acknowledgeAlert(alertId, acknowledgment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['alert'] });
      queryClient.invalidateQueries({ queryKey: ['alert-statistics'] });
      alertContext.success('Alert acknowledged successfully');
    },
    onError: (error: any) => {
      alertContext.error(`Failed to acknowledge alert: ${error.message}`);
    },
  });

  const startMonitoring = useMutation({
    mutationFn: (paths?: string[]) => alertsApi.startMonitoring(paths),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoring-status'] });
      alertContext.success('Monitoring started successfully');
    },
    onError: (error: any) => {
      alertContext.error(`Failed to start monitoring: ${error.message}`);
    },
  });

  const stopMonitoring = useMutation({
    mutationFn: () => alertsApi.stopMonitoring(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoring-status'] });
      alertContext.success('Monitoring stopped successfully');
    },
    onError: (error: any) => {
      alertContext.error(`Failed to stop monitoring: ${error.message}`);
    },
  });

  return {
    createConfiguration,
    updateConfiguration,
    deleteConfiguration,
    acknowledgeAlert,
    startMonitoring,
    stopMonitoring,
  };
};

export const useWebSocketNotifications = (userId?: string, filters?: Record<string, any>) => {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [shouldReconnect, setShouldReconnect] = useState(true);
  const alertContext = useAlert();

  const connect = useCallback(() => {
    // Don't attempt to connect if we shouldn't reconnect or already connecting
    if (!shouldReconnect || connectionStatus === 'connecting') {
      return;
    }

    // Don't reconnect if we've tried too many times
    if (reconnectAttempts >= 3) {
      console.log('Max reconnection attempts reached. Falling back to polling mode.');
      setShouldReconnect(false);
      setConnectionStatus('polling'); // New status for polling mode
      return;
    }

    try {
      // Check if we have an auth token before attempting to connect
      const token = localStorage.getItem('auth_token');
      if (!token) {
        console.warn('No authentication token available. Cannot establish WebSocket connection.');
        setConnectionStatus('disconnected');
        setShouldReconnect(false);
        return;
      }

      setConnectionStatus('connecting');
      const ws = alertsApi.createWebSocketConnection(userId, filters);
      
      ws.onopen = () => {
        setConnectionStatus('connected');
        setReconnectAttempts(0); // Reset attempts on successful connection
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const notification = JSON.parse(event.data);
          
          if (notification.type === 'connection_established') {
            console.log('WebSocket connection established:', notification.connection_id);
            return;
          }

          if (notification.type === 'pong') {
            return; // Handle ping/pong
          }

          // Add notification to list
          setNotifications(prev => [notification, ...prev.slice(0, 99)]); // Keep last 100 notifications

          // Show toast notification based on type and severity
          if (notification.type === 'alert_triggered') {
            if (notification.severity === 'critical') {
              alertContext.error(notification.message);
            } else if (notification.severity === 'high') {
              alertContext.warning(notification.message);
            } else {
              alertContext.info(notification.message);
            }
          } else if (notification.type === 'permission_change') {
            if (notification.message.includes('granted')) {
              alertContext.info(`🔓 ${notification.message}`);
            } else {
              alertContext.warning(`🚫 ${notification.message}`);
            }
          } else if (notification.type === 'group_membership_change') {
            alertContext.info(`👥 ${notification.message}`);
          }

        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        setConnectionStatus('disconnected');
        console.log('WebSocket disconnected', event.code, event.reason);
        
        // Handle authentication errors
        if (event.code === 1008) {
          console.error('WebSocket authentication failed:', event.reason);
          alertContext.error('WebSocket authentication failed. Please check your login status.');
          setShouldReconnect(false); // Don't retry on auth failures
          return;
        }
        
        // Only reconnect if it was a normal closure and we should reconnect
        if (shouldReconnect && websocket === ws && event.code !== 1000) {
          setReconnectAttempts(prev => prev + 1);
          const delay = Math.min(5000 * (reconnectAttempts + 1), 30000); // Exponential backoff up to 30s
          setTimeout(() => {
            if (websocket === ws) { // Only reconnect if this is still the current websocket
              connect();
            }
          }, delay);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('disconnected');
        // Don't log errors repeatedly during reconnection attempts
        if (reconnectAttempts === 0) {
          console.error('WebSocket connection failed. Will retry...');
        }
      };

      setWebsocket(ws);
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus('disconnected');
    }
  }, [userId, filters, alertContext, reconnectAttempts, shouldReconnect, connectionStatus]);

  const disconnect = useCallback(() => {
    setShouldReconnect(false); // Prevent reconnection
    if (websocket) {
      websocket.close(1000, 'User disconnected'); // Normal closure
      setWebsocket(null);
      setConnectionStatus('disconnected');
    }
  }, [websocket]);

  const sendMessage = useCallback((message: any) => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify(message));
    }
  }, [websocket]);

  const ping = useCallback(() => {
    sendMessage({ type: 'ping' });
  }, [sendMessage]);

  const updateFilters = useCallback((newFilters: Record<string, any>) => {
    sendMessage({ type: 'update_filters', filters: newFilters });
  }, [sendMessage]);

  const acknowledgeNotification = useCallback((notificationId: string) => {
    sendMessage({ type: 'acknowledge_notification', notification_id: notificationId });
    
    // Mark notification as read locally
    setNotifications(prev =>
      prev.map(notif =>
        notif.id === notificationId ? { ...notif, read: true } : notif
      )
    );
  }, [sendMessage]);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Ping every 30 seconds to keep connection alive
  useEffect(() => {
    if (connectionStatus === 'connected') {
      const pingInterval = setInterval(ping, 30000);
      return () => clearInterval(pingInterval);
    }
  }, [connectionStatus, ping]);

  // Polling fallback when WebSocket fails
  const { data: pollingAlerts } = useQuery({
    queryKey: ['alerts', 'polling-fallback'],
    queryFn: () => alertsApi.getAlerts({
      acknowledged: false,
      hours: 1,
      limit: 20
    }),
    refetchInterval: connectionStatus !== 'connected' ? 10000 : false, // Poll every 10 seconds when WebSocket is not connected
    enabled: connectionStatus !== 'connected'
  });

  // Handle polling alerts
  const [lastPolledAlertId, setLastPolledAlertId] = useState<number | null>(null);
  
  useEffect(() => {
    if (connectionStatus !== 'connected' && pollingAlerts?.length) {
      const latestAlert = pollingAlerts[0];
      
      if (lastPolledAlertId === null) {
        setLastPolledAlertId(latestAlert.id);
        return;
      }

      if (latestAlert.id > lastPolledAlertId) {
        const newAlerts = pollingAlerts.filter(alert => alert.id > lastPolledAlertId);
        
        // Convert to notifications and add them
        const newNotifications = newAlerts.map(alert => ({
          id: `alert-${alert.id}`,
          type: 'alert_triggered',
          title: `Alert: ${alert.severity.toUpperCase()}`,
          message: alert.message,
          severity: alert.severity,
          timestamp: alert.created_at,
          data: { alert_id: alert.id },
          read: false
        }));

        setNotifications(prev => [...newNotifications, ...prev.slice(0, 99)]);

        // Show toast notifications
        newNotifications.forEach(notification => {
          if (notification.severity === 'critical') {
            alertContext.error(`🚨 ${notification.message}`);
          } else if (notification.severity === 'high') {
            alertContext.warning(`⚠️ ${notification.message}`);
          } else {
            alertContext.info(`ℹ️ ${notification.message}`);
          }
        });

        setLastPolledAlertId(latestAlert.id);
      }
    }
  }, [pollingAlerts, lastPolledAlertId, connectionStatus, alertContext]);

  return {
    notifications,
    connectionStatus,
    connect,
    disconnect,
    sendMessage,
    updateFilters,
    acknowledgeNotification,
    clearNotifications,
    unreadCount: notifications.filter(n => !n.read).length
  };
};