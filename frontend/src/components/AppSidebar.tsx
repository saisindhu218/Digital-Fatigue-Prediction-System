import { LayoutDashboard, BarChart3, Sparkles, Lightbulb, Smartphone, UserCircle2, LogOut, Moon, Sun } from 'lucide-react';
import { NavLink } from '@/components/NavLink';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarMenu,
  SidebarMenuButton, SidebarMenuItem, SidebarFooter, useSidebar,
} from '@/components/ui/sidebar';

const navItems = [
  { title: 'Dashboard', url: '/dashboard', icon: LayoutDashboard },
  { title: 'Analytics', url: '/analytics', icon: BarChart3 },
  { title: 'AI Predictions', url: '/predictions', icon: Sparkles },
  { title: 'Recommendations', url: '/recommendations', icon: Lightbulb },
  { title: 'Device Pairing', url: '/devices', icon: Smartphone },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === 'collapsed';
  const { logout, user } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <Sidebar collapsible="icon">
      <SidebarContent>
        {/* Logo */}
        <div className="p-4 flex items-center">
          {!collapsed && (
            <span className="inline-flex items-center rounded-md bg-primary/10 px-2.5 py-1 text-sm font-semibold tracking-tight text-primary ring-1 ring-primary/15">
              FatigueAI
            </span>
          )}
        </div>

        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.url}
                      end
                      className="hover:bg-sidebar-accent/50"
                      activeClassName="bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    >
                      <item.icon className="w-4 h-4 mr-2 shrink-0" />
                      {!collapsed && <span>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-3">
        {!collapsed && user && (
          <NavLink
            to="/profile"
            className="flex items-center gap-2 px-2 py-2 mb-2 rounded-md text-sm font-medium truncate hover:bg-sidebar-accent/60"
            activeClassName="bg-sidebar-accent text-sidebar-accent-foreground"
          >
            <UserCircle2 className="w-4 h-4 shrink-0" />
            <span className="truncate">{user.name || user.email}</span>
          </NavLink>
        )}
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={toggleTheme} className="hover:bg-sidebar-accent/60">
              {theme === 'dark' ? (
                <Sun className="w-4 h-4 mr-2" />
              ) : (
                <Moon className="w-4 h-4 mr-2" />
              )}
              {!collapsed && <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>}
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={logout} className="hover:bg-destructive/10 hover:text-destructive">
              <LogOut className="w-4 h-4 mr-2" />
              {!collapsed && <span>Sign Out</span>}
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
