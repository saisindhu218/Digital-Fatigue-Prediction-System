import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { api } from '@/lib/api';

export interface Notification {
  notification_id: string;
  timestamp: string;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  action_url?: string;
}

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  addNotification: (notification: Notification) => void;
  removeNotification: (notificationId: string) => Promise<void>;
  markAsRead: (notificationId: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  clearAll: () => Promise<void>;
  fetchNotifications: () => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      const data = await api.getNotifications(50, false) as Notification[];
      setNotifications(data);
      const unread = data.filter((n: Notification) => !n.is_read).length;
      setUnreadCount(unread);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      setNotifications([]);
      setUnreadCount(0);
    }
  }, [isAuthenticated]);

  const addNotification = (notification: Notification) => {
    setNotifications(prev => [notification, ...prev]);
    if (!notification.is_read) {
      setUnreadCount(prev => prev + 1);
    }
  };

  const removeNotification = async (notificationId: string) => {
    if (!isAuthenticated) return;

    try {
      await api.deleteNotification(notificationId);
      setNotifications(prev => prev.filter(n => n.notification_id !== notificationId));
      setUnreadCount(prev => {
        const deleted = notifications.find(n => n.notification_id === notificationId);
        if (deleted && !deleted.is_read) {
          return Math.max(0, prev - 1);
        }
        return prev;
      });
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  const markAsRead = async (notificationId: string) => {
    if (!isAuthenticated) return;

    try {
      await api.markNotificationAsRead(notificationId);
      setNotifications(prev =>
        prev.map(n =>
          n.notification_id === notificationId ? { ...n, is_read: true } : n
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    if (!isAuthenticated) return;

    try {
      await api.markAllNotificationsAsRead();
      setNotifications(prev =>
        prev.map(n => ({ ...n, is_read: true }))
      );
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const clearAll = async () => {
    if (!isAuthenticated) return;

    try {
      await api.deleteAllNotifications();
      setNotifications([]);
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to clear notifications:', error);
    }
  };

  // Fetch notifications on mount and when token changes
  useEffect(() => {
    if (isAuthenticated) {
      fetchNotifications();
      
      // Polling interval - refresh every 30 seconds
      const interval = setInterval(fetchNotifications, 30000);
      return () => clearInterval(interval);
    } else {
      setNotifications([]);
      setUnreadCount(0);
    }
  }, [isAuthenticated, fetchNotifications]);

  const value: NotificationContextType = {
    notifications,
    unreadCount,
    addNotification,
    removeNotification,
    markAsRead,
    markAllAsRead,
    clearAll,
    fetchNotifications,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};
