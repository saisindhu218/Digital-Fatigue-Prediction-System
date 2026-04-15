import { LayoutDashboard, BarChart3, Sparkles, Lightbulb, Smartphone, LogOut } from 'lucide-react';
import { NavLink } from '@/components/NavLink';
import { useAuth } from '@/contexts/AuthContext';
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
          <div className="px-2 py-1.5 mb-2">
            <p className="text-xs font-medium truncate">{user.name || user.email}</p>
            <p className="text-[10px] text-muted-foreground truncate">{user.email}</p>
          </div>
        )}
        <SidebarMenu>
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
