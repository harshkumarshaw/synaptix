"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from "@/components/ui/sidebar";
import {
  LayoutDashboard,
  CalendarCheck,
  BookOpen,
  GraduationCap,
  FileText,
  ClipboardList,
  Users,
  Settings,
  Stethoscope,
  LogOut,
  UserCircle,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";

const NAV_ITEMS = {
  admin: [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "Attendance", href: "/attendance", icon: CalendarCheck },
    { label: "Logbook", href: "/logbook", icon: BookOpen },
    { label: "DOAP Skills", href: "/doap", icon: Stethoscope },
    { label: "Electives", href: "/electives", icon: GraduationCap },
    { label: "Leave Requests", href: "/leave", icon: FileText },
    { label: "Admissions", href: "/admissions", icon: ClipboardList },
    { label: "Faculty & Students", href: "/people", icon: Users },
    { label: "Settings", href: "/settings", icon: Settings },
  ],
  faculty: [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "Mark Attendance", href: "/attendance", icon: CalendarCheck },
    { label: "Logbook Reviews", href: "/logbook", icon: BookOpen },
    { label: "DOAP Records", href: "/doap", icon: Stethoscope },
    { label: "Leave Requests", href: "/leave", icon: FileText },
  ],
  hod: [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "Attendance", href: "/attendance", icon: CalendarCheck },
    { label: "Logbook Reviews", href: "/logbook", icon: BookOpen },
    { label: "DOAP Records", href: "/doap", icon: Stethoscope },
    { label: "Electives", href: "/electives", icon: GraduationCap },
    { label: "Leave Approvals", href: "/leave", icon: FileText },
    { label: "Department", href: "/department", icon: Users },
  ],
  student: [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "My Attendance", href: "/attendance", icon: CalendarCheck },
    { label: "My Logbook", href: "/logbook", icon: BookOpen },
    { label: "DOAP Progress", href: "/doap", icon: Stethoscope },
    { label: "Electives", href: "/electives", icon: GraduationCap },
    { label: "Leave Requests", href: "/leave", icon: FileText },
  ],
} as const;

export function AppSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const role = user?.role ?? "student";
  const items = NAV_ITEMS[role as keyof typeof NAV_ITEMS] ?? NAV_ITEMS.student;

  return (
    <Sidebar>
      <SidebarHeader className="border-b px-4 py-4">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground font-bold text-sm">
            S
          </div>
          <div>
            <p className="text-sm font-semibold">Synaptix</p>
            <p className="text-xs text-muted-foreground">JMN Medical College</p>
          </div>
        </Link>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarMenu>
            {items.map((item) => (
              <SidebarMenuItem key={item.href}>
                <SidebarMenuButton
                  isActive={pathname === item.href}
                  render={
                    <Link href={item.href} className="flex items-center gap-3">
                      <item.icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  }
                />
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t p-4">
        <div className="flex items-center gap-3">
          <UserCircle className="h-8 w-8 text-muted-foreground" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.name}</p>
            <p className="text-xs text-muted-foreground capitalize">{role}</p>
          </div>
          <button
            onClick={() => {
              logout();
              window.location.href = "/login";
            }}
            className="text-muted-foreground hover:text-foreground"
            title="Sign out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
