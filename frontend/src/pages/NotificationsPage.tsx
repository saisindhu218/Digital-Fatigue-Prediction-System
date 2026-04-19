import React, { useEffect, useState } from 'react';
import { useNotifications } from '../contexts/NotificationContext';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import {
  Bell,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Info,
  TrendingUp,
  Calendar,
  X,
} from 'lucide-react';

const NotificationsPage: React.FC = () => {
  const navigate = useNavigate();
  const { notifications, markAsRead, removeNotification, markAllAsRead, clearAll, unreadCount } =
    useNotifications();

  const [filteredType, setFilteredType] = useState<string>('all');
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'break':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'fatigue_alert':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'productivity_alert':
        return <TrendingUp className="w-5 h-5 text-orange-500" />;
      case 'recommendation':
        return <Info className="w-5 h-5 text-blue-500" />;
      case 'weekly_digest':
        return <Calendar className="w-5 h-5 text-purple-500" />;
      default:
        return <Bell className="w-5 h-5 text-gray-500" />;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'break':
        return 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800';
      case 'fatigue_alert':
        return 'bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800';
      case 'productivity_alert':
        return 'bg-orange-50 dark:bg-orange-950 border-orange-200 dark:border-orange-800';
      case 'recommendation':
        return 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800';
      case 'weekly_digest':
        return 'bg-purple-50 dark:bg-purple-950 border-purple-200 dark:border-purple-800';
      default:
        return 'bg-gray-50 dark:bg-gray-950 border-gray-200 dark:border-gray-800';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
  };

  const filteredNotifications = notifications.filter(notif => {
    if (filteredType !== 'all' && notif.type !== filteredType) return false;
    if (showUnreadOnly && notif.is_read) return false;
    return true;
  });

  const notificationTypes = [
    { value: 'all', label: 'All', count: notifications.length },
    { value: 'break', label: 'Breaks', count: notifications.filter(n => n.type === 'break').length },
    {
      value: 'fatigue_alert',
      label: 'Fatigue',
      count: notifications.filter(n => n.type === 'fatigue_alert').length,
    },
    {
      value: 'productivity_alert',
      label: 'Productivity',
      count: notifications.filter(n => n.type === 'productivity_alert').length,
    },
    {
      value: 'recommendation',
      label: 'Recommendations',
      count: notifications.filter(n => n.type === 'recommendation').length,
    },
    {
      value: 'weekly_digest',
      label: 'Digests',
      count: notifications.filter(n => n.type === 'weekly_digest').length,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-blue-50 to-slate-100 dark:from-slate-950 dark:via-blue-950 dark:to-slate-950 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Bell className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            <h1 className="text-4xl font-bold text-slate-900 dark:text-white">Notifications</h1>
          </div>
          <p className="text-slate-600 dark:text-slate-400">
            {unreadCount > 0 ? `You have ${unreadCount} unread notification${unreadCount !== 1 ? 's' : ''}` : 'All caught up!'}
          </p>
        </div>

        {/* Filter & Actions */}
        <Card className="mb-6 border-slate-200 dark:border-slate-800 glass-card">
          <CardHeader className="pb-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">
                  Filter
                </h2>
                <div className="flex flex-wrap gap-2">
                  {notificationTypes.map(type => (
                    <Button
                      key={type.value}
                      onClick={() => setFilteredType(type.value)}
                      variant={filteredType === type.value ? 'default' : 'outline'}
                      className="text-sm"
                    >
                      {type.label}
                      <Badge
                        variant="secondary"
                        className="ml-2 bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-white"
                      >
                        {type.count}
                      </Badge>
                    </Button>
                  ))}
                </div>
              </div>

              {/* Unread Only Toggle */}
              <div className="flex items-center gap-3 p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Unread Only
                </span>
                <Switch checked={showUnreadOnly} onCheckedChange={setShowUnreadOnly} />
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Actions Bar */}
        {unreadCount > 0 && (
          <div className="flex gap-2 mb-6">
            <Button
              onClick={() => markAllAsRead()}
              variant="outline"
              className="bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800 hover:bg-blue-100 dark:hover:bg-blue-900"
            >
              Mark All as Read
            </Button>
          </div>
        )}

        {/* Notifications List */}
        <div className="space-y-3">
          {filteredNotifications.length === 0 ? (
            <Card className="border-slate-200 dark:border-slate-800 glass-card">
              <CardContent className="pt-8 pb-8 text-center">
                <Bell className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto mb-4" />
                <p className="text-slate-500 dark:text-slate-400 text-lg">No notifications yet</p>
              </CardContent>
            </Card>
          ) : (
            filteredNotifications.map(notification => (
              <div
                key={notification.notification_id}
                className={`border rounded-lg p-4 flex items-start gap-4 transition-all ${getNotificationColor(
                  notification.type
                )} ${!notification.is_read ? 'ring-2 ring-blue-400 dark:ring-blue-600' : ''}`}
              >
                {/* Icon */}
                <div className="flex-shrink-0 mt-1">{getNotificationIcon(notification.type)}</div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <h3 className="font-semibold text-slate-900 dark:text-white text-sm">
                        {notification.title}
                      </h3>
                      <p className="text-slate-700 dark:text-slate-300 text-sm mt-1 line-clamp-2">
                        {notification.message}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-slate-500 dark:text-slate-400">
                          {formatTime(notification.timestamp)}
                        </span>
                        {!notification.is_read && (
                          <span className="inline-block w-2 h-2 bg-blue-500 rounded-full"></span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  {notification.action_url && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => navigate(notification.action_url || '/')}
                      className="text-xs h-8"
                    >
                      View
                    </Button>
                  )}
                  {!notification.is_read && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => markAsRead(notification.notification_id)}
                      className="text-xs h-8"
                    >
                      ✓
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => removeNotification(notification.notification_id)}
                    className="text-xs h-8 text-red-500 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Clear All Button */}
        {notifications.length > 0 && (
          <div className="mt-8 pt-6 border-t border-slate-200 dark:border-slate-800 flex justify-center">
            <Button
              onClick={() => {
                if (window.confirm('Are you sure you want to clear all notifications?')) {
                  clearAll();
                }
              }}
              variant="destructive"
              className="opacity-70 hover:opacity-100"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Clear All Notifications
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationsPage;
