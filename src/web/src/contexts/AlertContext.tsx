import React, { createContext, useContext, ReactNode } from 'react';
import toast, { Toaster } from 'react-hot-toast';

export interface NotificationService {
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
  warning: (message: string) => void;
  permissionGranted: (user: string, path: string, permission: string) => void;
  permissionRevoked: (user: string, path: string, permission: string) => void;
}

const AlertContext = createContext<NotificationService | null>(null);

export const useAlert = (): NotificationService => {
  const context = useContext(AlertContext);
  if (!context) {
    throw new Error('useAlert must be used within an AlertProvider');
  }
  return context;
};

interface AlertProviderProps {
  children: ReactNode;
}

export const AlertProvider: React.FC<AlertProviderProps> = ({ children }) => {
  const notificationService: NotificationService = {
    success: (message: string) => {
      toast.success(message, {
        duration: 4000,
        position: 'top-right',
      });
    },

    error: (message: string) => {
      toast.error(message, {
        duration: 6000,
        position: 'top-right',
      });
    },

    info: (message: string) => {
      toast(message, {
        duration: 4000,
        position: 'top-right',
        icon: '9',
      });
    },

    warning: (message: string) => {
      toast(message, {
        duration: 5000,
        position: 'top-right',
        icon: '�',
        style: {
          background: '#f59e0b',
          color: 'white',
        },
      });
    },

    permissionGranted: (user: string, path: string, permission: string) => {
      toast.success(
        ` Permission granted: ${user} now has ${permission} access to ${path}`,
        {
          duration: 6000,
          position: 'top-right',
        }
      );
    },

    permissionRevoked: (user: string, path: string, permission: string) => {
      toast.error(
        `=� Permission revoked: ${user} no longer has ${permission} access to ${path}`,
        {
          duration: 6000,
          position: 'top-right',
        }
      );
    },
  };

  return (
    <AlertContext.Provider value={notificationService}>
      {children}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
            zIndex: 9999,
          },
          success: {
            duration: 4000,
            style: {
              background: '#10b981',
              color: '#fff',
              zIndex: 9999,
            },
          },
          error: {
            duration: 6000,
            style: {
              background: '#ef4444',
              color: '#fff',
              zIndex: 9999,
            },
          },
        }}
        containerStyle={{
          zIndex: 9999,
        }}
      />
    </AlertContext.Provider>
  );
};