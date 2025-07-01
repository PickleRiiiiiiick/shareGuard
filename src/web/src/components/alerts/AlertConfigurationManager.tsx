// src/web/src/components/alerts/AlertConfigurationManager.tsx

import React, { useState } from 'react';
import {
  AlertConfiguration,
  AlertConfigurationCreate,
  AlertConfigurationUpdate,
  AlertType,
  AlertSeverity
} from '../../types/alerts';
import { useAlertConfigurations, useAlertMutations } from '../../hooks/useAlerts';
import { useTargets } from '../../hooks/useTargets';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface AlertConfigurationManagerProps {
  className?: string;
}

const AlertConfigurationManager: React.FC<AlertConfigurationManagerProps> = ({ className = '' }) => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingConfig, setEditingConfig] = useState<AlertConfiguration | null>(null);
  const [filter, setFilter] = useState<{ is_active?: boolean; target_id?: number }>({});

  const { configurations, isLoading, error, refetch } = useAlertConfigurations(filter);
  const { targets } = useTargets();
  const {
    createConfiguration,
    updateConfiguration,
    deleteConfiguration
  } = useAlertMutations();

  const handleCreateConfig = async (config: AlertConfigurationCreate) => {
    try {
      await createConfiguration.mutateAsync(config);
      setShowCreateForm(false);
      refetch();
    } catch (error) {
      console.error('Failed to create configuration:', error);
    }
  };

  const handleUpdateConfig = async (configId: number, update: AlertConfigurationUpdate) => {
    try {
      await updateConfiguration.mutateAsync({ configId, update });
      setEditingConfig(null);
      refetch();
    } catch (error) {
      console.error('Failed to update configuration:', error);
    }
  };

  const handleDeleteConfig = async (configId: number) => {
    if (window.confirm('Are you sure you want to delete this alert configuration?')) {
      try {
        await deleteConfiguration.mutateAsync(configId);
        refetch();
      } catch (error) {
        console.error('Failed to delete configuration:', error);
      }
    }
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
        <h3 className="text-red-800 font-medium">Error Loading Configurations</h3>
        <p className="text-red-600 text-sm mt-1">{error.message}</p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Alert Configurations</h2>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Create Configuration
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4 bg-white p-4 rounded-lg border border-gray-200">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select
            value={filter.is_active === undefined ? '' : filter.is_active.toString()}
            onChange={(e) => setFilter(prev => ({
              ...prev,
              is_active: e.target.value === '' ? undefined : e.target.value === 'true'
            }))}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Target</label>
          <select
            value={filter.target_id || ''}
            onChange={(e) => setFilter(prev => ({
              ...prev,
              target_id: e.target.value ? Number(e.target.value) : undefined
            }))}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Targets</option>
            {targets?.map(target => (
              <option key={target.id} value={target.id}>{target.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Configurations List */}
      <div className="bg-white rounded-lg border border-gray-200">
        {configurations.length === 0 ? (
          <div className="p-8 text-center">
            <span className="text-6xl">🔕</span>
            <h3 className="text-lg font-medium text-gray-900 mt-4">No Alert Configurations</h3>
            <p className="text-gray-600 mt-2">Create your first alert configuration to get started.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {configurations.map((config) => (
              <ConfigurationRow
                key={config.id}
                configuration={config}
                isEditing={editingConfig?.id === config.id}
                onEdit={() => setEditingConfig(config)}
                onCancelEdit={() => setEditingConfig(null)}
                onSave={(update) => handleUpdateConfig(config.id, update)}
                onDelete={() => handleDeleteConfig(config.id)}
                targets={targets || []}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create Configuration Modal */}
      {showCreateForm && (
        <CreateConfigurationModal
          onSave={handleCreateConfig}
          onCancel={() => setShowCreateForm(false)}
          targets={targets || []}
        />
      )}
    </div>
  );
};

// Configuration Row Component
interface ConfigurationRowProps {
  configuration: AlertConfiguration;
  isEditing: boolean;
  onEdit: () => void;
  onCancelEdit: () => void;
  onSave: (update: AlertConfigurationUpdate) => void;
  onDelete: () => void;
  targets: any[];
}

const ConfigurationRow: React.FC<ConfigurationRowProps> = ({
  configuration,
  isEditing,
  onEdit,
  onCancelEdit,
  onSave,
  onDelete,
  targets
}) => {
  const [editForm, setEditForm] = useState<AlertConfigurationUpdate>({
    name: configuration.name,
    alert_type: configuration.alert_type,
    severity: configuration.severity,
    conditions: configuration.conditions,
    notifications: configuration.notifications,
    is_active: configuration.is_active
  });

  const getSeverityColor = (severity: AlertSeverity) => {
    switch (severity) {
      case AlertSeverity.CRITICAL: return 'bg-red-100 text-red-800';
      case AlertSeverity.HIGH: return 'bg-orange-100 text-orange-800';
      case AlertSeverity.MEDIUM: return 'bg-yellow-100 text-yellow-800';
      case AlertSeverity.LOW: return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleSave = () => {
    onSave(editForm);
  };

  if (isEditing) {
    return (
      <div className="p-6 bg-gray-50">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              value={editForm.name || ''}
              onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Alert Type</label>
            <select
              value={editForm.alert_type || ''}
              onChange={(e) => setEditForm(prev => ({ ...prev, alert_type: e.target.value as AlertType }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.values(AlertType).map(type => (
                <option key={type} value={type}>{type.replace(/_/g, ' ').toUpperCase()}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
            <select
              value={editForm.severity || ''}
              onChange={(e) => setEditForm(prev => ({ ...prev, severity: e.target.value as AlertSeverity }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.values(AlertSeverity).map(severity => (
                <option key={severity} value={severity}>{severity.toUpperCase()}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={editForm.is_active || false}
                onChange={(e) => setEditForm(prev => ({ ...prev, is_active: e.target.checked }))}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">Active</span>
            </label>
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-4">
          <button
            onClick={onCancelEdit}
            className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Save
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-medium text-gray-900">{configuration.name}</h3>
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(configuration.severity)}`}>
              {configuration.severity.toUpperCase()}
            </span>
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
              configuration.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
            }`}>
              {configuration.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
          
          <div className="mt-2 text-sm text-gray-600">
            <p>Type: {configuration.alert_type.replace(/_/g, ' ').toUpperCase()}</p>
            {configuration.target_name && <p>Target: {configuration.target_name}</p>}
            {configuration.statistics && (
              <p>Alerts: {configuration.statistics.total_alerts} total, {configuration.statistics.recent_alerts} recent</p>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={onEdit}
            className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
            title="Edit"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            onClick={onDelete}
            className="p-2 text-gray-400 hover:text-red-600 transition-colors"
            title="Delete"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

// Create Configuration Modal
interface CreateConfigurationModalProps {
  onSave: (config: AlertConfigurationCreate) => void;
  onCancel: () => void;
  targets: any[];
}

const CreateConfigurationModal: React.FC<CreateConfigurationModalProps> = ({
  onSave,
  onCancel,
  targets
}) => {
  const [form, setForm] = useState<AlertConfigurationCreate>({
    name: '',
    alert_type: AlertType.PERMISSION_CHANGE,
    severity: AlertSeverity.MEDIUM,
    is_active: true
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (form.name.trim()) {
      onSave(form);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Create Alert Configuration</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Target (Optional)</label>
            <select
              value={form.target_id || ''}
              onChange={(e) => setForm(prev => ({ ...prev, target_id: e.target.value ? Number(e.target.value) : undefined }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Targets</option>
              {targets.map(target => (
                <option key={target.id} value={target.id}>{target.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Alert Type</label>
            <select
              value={form.alert_type}
              onChange={(e) => setForm(prev => ({ ...prev, alert_type: e.target.value as AlertType }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.values(AlertType).map(type => (
                <option key={type} value={type}>{type.replace(/_/g, ' ').toUpperCase()}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
            <select
              value={form.severity}
              onChange={(e) => setForm(prev => ({ ...prev, severity: e.target.value as AlertSeverity }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.values(AlertSeverity).map(severity => (
                <option key={severity} value={severity}>{severity.toUpperCase()}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) => setForm(prev => ({ ...prev, is_active: e.target.checked }))}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">Active</span>
            </label>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AlertConfigurationManager;