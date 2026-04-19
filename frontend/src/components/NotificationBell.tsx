import { Bell, Check, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useNotifications } from '@/contexts/NotificationContext';

function formatTime(timestamp: string) {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return date.toLocaleDateString();
}

export function NotificationBell() {
  const navigate = useNavigate();
  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    removeNotification,
  } = useNotifications();

  const recentNotifications = notifications.slice(0, 8);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" aria-label="Open notifications">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-[360px] p-0">
        <div className="flex items-center justify-between px-3 py-2">
          <DropdownMenuLabel className="p-0">Notifications</DropdownMenuLabel>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={() => markAllAsRead()}
            >
              Mark all read
            </Button>
          )}
        </div>
        <DropdownMenuSeparator />

        <div className="max-h-96 overflow-y-auto">
          {recentNotifications.length === 0 ? (
            <div className="px-3 py-8 text-center text-sm text-muted-foreground">
              No notifications yet
            </div>
          ) : (
            recentNotifications.map((notification) => (
              <div
                key={notification.notification_id}
                className={`border-b border-border/50 px-3 py-2 ${!notification.is_read ? 'bg-primary/5' : ''}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <p className="truncate text-sm font-medium">{notification.title}</p>
                      {!notification.is_read && <Badge className="h-5 px-1.5 text-[10px]">New</Badge>}
                    </div>
                    <p className="line-clamp-2 text-xs text-muted-foreground">{notification.message}</p>
                    <div className="mt-1 text-[11px] text-muted-foreground">{formatTime(notification.timestamp)}</div>
                  </div>

                  <div className="flex items-center gap-1">
                    {notification.action_url && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 text-xs"
                        onClick={() => navigate(notification.action_url || '/')}
                      >
                        View
                      </Button>
                    )}
                    {!notification.is_read && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => markAsRead(notification.notification_id)}
                        aria-label="Mark notification as read"
                      >
                        <Check className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-red-500"
                      onClick={() => removeNotification(notification.notification_id)}
                      aria-label="Delete notification"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
