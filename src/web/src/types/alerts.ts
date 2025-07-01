// src/web/src/types/alerts.ts

export interface AlertConfiguration {
  id: number;
  target_id?: number;
  name: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  conditions?: Record<string, any>;
  notifications?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  target_name?: string;
  statistics?: {
    total_alerts: number;
    recent_alerts: number;
  };
}

export interface Alert {
  id: number;
  config_id: number;
  scan_job_id?: number;
  permission_change_id?: number;
  severity: AlertSeverity;
  message: string;
  details?: Record<string, any>;
  created_at: string;
  acknowledged_at?: string;
  acknowledged_by?: string;
  configuration_name?: string;
  target_name?: string;
  configuration?: {
    id: number;
    name: string;
    alert_type: AlertType;
    conditions?: Record<string, any>;
  };
  permission_change?: {
    id: number;
    change_type: string;
    previous_state?: Record<string, any>;
    current_state?: Record<string, any>;
    detected_time: string;
  };
}

export interface PermissionChange {
  id: number;
  change_type: string;
  detected_time: string;
  previous_state?: Record<string, any>;
  current_state?: Record<string, any>;
  scan_job_id: number;
}

export interface AlertStatistics {
  time_period_hours: number;
  total_alerts: number;
  unacknowledged_alerts: number;
  alerts_by_severity: Record<AlertSeverity, number>;
  alerts_by_type: Record<AlertType, number>;
  recent_changes: PermissionChange[];
}

export interface MonitoringStatus {
  change_monitoring_active: boolean;
  group_monitoring_active: boolean;
  group_monitoring_stats: {
    monitoring_active: boolean;
    groups_monitored: number;
    last_snapshot_times: Record<string, string>;
    configuration: {
      snapshot_interval: number;
      change_detection_interval: number;
      max_snapshot_age: number;
    };
    cache_stats: {
      snapshots_cached: number;
      memory_usage_estimate: number;
    };
  };
  notification_service_stats: {
    active_connections: number;
    unique_users: number;
    notifications_sent: number;
    notifications_queued: number;
    connections_established: number;
    connections_closed: number;
    queue_size: number;
  };
}

export interface WebSocketNotification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  severity: AlertSeverity;
  timestamp: string;
  data: Record<string, any>;
  read: boolean;
}

export interface WebSocketFilters {
  types?: NotificationType[];
  min_severity?: AlertSeverity;
  paths?: string[];
}

export enum AlertType {
  PERMISSION_CHANGE = 'permission_change',
  NEW_ACCESS = 'new_access',
  INHERITANCE_CHANGE = 'inheritance_change',
  GROUP_MEMBERSHIP_CHANGE = 'group_membership_change',
  SENSITIVE_ACCESS = 'sensitive_access'
}

export enum AlertSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum NotificationType {
  PERMISSION_CHANGE = 'permission_change',
  GROUP_MEMBERSHIP_CHANGE = 'group_membership_change',
  NEW_ACCESS_GRANTED = 'new_access_granted',
  ACCESS_REMOVED = 'access_removed',
  ALERT_TRIGGERED = 'alert_triggered',
  SYSTEM_STATUS = 'system_status'
}

export interface AlertConfigurationCreate {
  target_id?: number;
  name: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  conditions?: Record<string, any>;
  notifications?: Record<string, any>;
  is_active?: boolean;
}

export interface AlertConfigurationUpdate {
  name?: string;
  alert_type?: AlertType;
  severity?: AlertSeverity;
  conditions?: Record<string, any>;
  notifications?: Record<string, any>;
  is_active?: boolean;
}

export interface AlertAcknowledge {
  acknowledged_by: string;
  notes?: string;
}

export interface AlertsFilters {
  acknowledged?: boolean;
  severity?: AlertSeverity;
  alert_type?: AlertType;
  hours?: number;
  skip?: number;
  limit?: number;
}

export interface RecentChangesFilters {
  hours?: number;
  change_types?: string;
  skip?: number;
  limit?: number;
}