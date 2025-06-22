import React from 'react';
import { useAlert } from '@/contexts/AlertContext';

export function PermissionNotificationTest() {
  const alert = useAlert();

  const testNotifications = () => {
    console.log('Testing notifications...', alert);
    
    try {
      // Test permission granted notification
      console.log('Calling permissionGranted...');
      alert.permissionGranted('DOMAIN\\testuser', 'C:\\TestFolder', 'read, write');
      
      // Test permission revoked notification after 2 seconds
      setTimeout(() => {
        console.log('Calling permissionRevoked...');
        alert.permissionRevoked('DOMAIN\\testuser', 'C:\\TestFolder', 'write');
      }, 2000);
      
      // Test generic success after 4 seconds
      setTimeout(() => {
        console.log('Calling success...');
        alert.success('Permission change complete');
      }, 4000);
      
      // Test simple info immediately
      console.log('Calling info...');
      alert.info('Testing notification system');
      
    } catch (error) {
      console.error('Error calling notifications:', error);
    }
  };

  return (
    <div className="p-4 border rounded-lg bg-gray-50">
      <h3 className="text-lg font-medium mb-2">Test Notifications</h3>
      <p className="text-sm text-gray-600 mb-4">
        Click the button below to test the permission notification system
      </p>
      <button
        onClick={testNotifications}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        Test Permission Notifications
      </button>
    </div>
  );
}