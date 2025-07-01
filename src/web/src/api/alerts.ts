// src/web/src/api/alerts.ts

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
import { api } from '../utils/api';

export const alertsApi = {
  // Alert Configuration endpoints
  async createConfiguration(config: AlertConfigurationCreate): Promise<AlertConfiguration> {
    return api.alerts.post<AlertConfiguration>('/configurations', config);
  },

  async getConfigurations(params?: {
    target_id?: number;
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<AlertConfiguration[]> {
    const searchParams = new URLSearchParams();
    if (params?.target_id !== undefined) searchParams.append('target_id', params.target_id.toString());
    if (params?.is_active !== undefined) searchParams.append('is_active', params.is_active.toString());
    if (params?.skip !== undefined) searchParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) searchParams.append('limit', params.limit.toString());
    
    return api.alerts.get<AlertConfiguration[]>(`/configurations${searchParams.toString() ? `?${searchParams.toString()}` : ''}`);
  },

  async getConfiguration(configId: number): Promise<AlertConfiguration> {
    return api.alerts.get<AlertConfiguration>(`/configurations/${configId}`);
  },

  async updateConfiguration(configId: number, update: AlertConfigurationUpdate): Promise<AlertConfiguration> {
    return api.alerts.put<AlertConfiguration>(`/configurations/${configId}`, update);
  },

  async deleteConfiguration(configId: number): Promise<{ message: string }> {
    return api.alerts.delete<{ message: string }>(`/configurations/${configId}`);
  },

  // Alert management endpoints
  async getAlerts(filters?: AlertsFilters): Promise<Alert[]> {
    const searchParams = new URLSearchParams();
    if (filters?.acknowledged !== undefined) searchParams.append('acknowledged', filters.acknowledged.toString());
    if (filters?.severity) searchParams.append('severity', filters.severity);
    if (filters?.alert_type) searchParams.append('alert_type', filters.alert_type);
    if (filters?.hours !== undefined) searchParams.append('hours', filters.hours.toString());
    if (filters?.skip !== undefined) searchParams.append('skip', filters.skip.toString());
    if (filters?.limit !== undefined) searchParams.append('limit', filters.limit.toString());
    
    return api.alerts.get<Alert[]>(`/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`);
  },

  async getAlert(alertId: number): Promise<Alert> {
    return api.alerts.get<Alert>(`/${alertId}`);
  },

  async acknowledgeAlert(alertId: number, acknowledgment: AlertAcknowledge): Promise<{ message: string }> {
    return api.alerts.post<{ message: string }>(`/${alertId}/acknowledge`, acknowledgment);
  },

  // Statistics and dashboard endpoints
  async getStatistics(hours: number = 24): Promise<AlertStatistics> {
    return api.alerts.get<AlertStatistics>(`/statistics/summary?hours=${hours}`);
  },

  // Change monitoring endpoints
  async getRecentChanges(filters?: RecentChangesFilters): Promise<PermissionChange[]> {
    const searchParams = new URLSearchParams();
    if (filters?.hours !== undefined) searchParams.append('hours', filters.hours.toString());
    if (filters?.change_types) searchParams.append('change_types', filters.change_types);
    if (filters?.skip !== undefined) searchParams.append('skip', filters.skip.toString());
    if (filters?.limit !== undefined) searchParams.append('limit', filters.limit.toString());
    
    return api.alerts.get<PermissionChange[]>(`/changes/recent${searchParams.toString() ? `?${searchParams.toString()}` : ''}`);
  },

  async startMonitoring(paths?: string[]): Promise<{ message: string; monitoring_paths: string | string[] }> {
    return api.alerts.post<{ message: string; monitoring_paths: string | string[] }>('/monitoring/start', paths ? { paths } : null);
  },

  async stopMonitoring(): Promise<{ message: string }> {
    return api.alerts.post<{ message: string }>('/monitoring/stop', {});
  },

  async getMonitoringStatus(): Promise<MonitoringStatus> {
    return api.alerts.get<MonitoringStatus>('/monitoring/status');
  },

  // WebSocket connection helper
  createWebSocketConnection(userId?: string, filters?: Record<string, any>): WebSocket {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Connect to backend server on port 8000
    const host = 'localhost:8000';
    
    const searchParams = new URLSearchParams();
    if (userId) searchParams.append('user_id', userId);
    if (filters) searchParams.append('filters', JSON.stringify(filters));
    
    const url = `${protocol}//${host}/api/v1/alerts/notifications${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    
    return new WebSocket(url);
  },
};