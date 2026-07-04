# Session F1 Plan — Frontend Scaffold: Auth + Layout + Dashboard

**Target Agent:** 03-frontend
**Estimated duration:** 4-6 hours
**Goal:** By the end of this session, you can open a browser, log in, see a dashboard, and navigate between pages. First visible UI of the entire project.
**Tech:** Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui

---

## Why This Session Matters

14 sessions of backend work. Zero UI. This session changes that. After this session, you open `http://localhost:3000`, see a login page, enter credentials, and land on a role-specific dashboard with navigation. Nothing fancy — but real, visible, clickable.

The psychological effect of seeing a UI after 14 backend sessions is significant. It makes the project feel real in a way that passing tests don't. Lean into that.

---

## Mandatory Session Start Protocol

This is the FIRST frontend session. The agent must:

1. Read `AGENTS.md` (root)
2. Read `agents/03-frontend-agent.md`
3. Read `docs/HANDOFF_NOTES.md`
4. Read `.agent-memory/working/CURRENT_FOCUS.md`
5. Read `docs/PHASE2_SCHEMA.md` — understand the data model (the UI renders this data)
6. Read `conventions/API_DESIGN.md` — understand the API patterns the frontend calls
7. Read `conventions/CODING_STANDARDS.md` — TypeScript section

**Declaration:**
```
SESSION START — Agent: 03-frontend (Session F1)
Files read: AGENTS.md ✓, frontend agent spec ✓, HANDOFF_NOTES ✓, CURRENT_FOCUS ✓,
PHASE2_SCHEMA.md ✓ (understand backend data model), API_DESIGN ✓, CODING_STANDARDS ✓
Task: Frontend scaffold — Next.js 14 project, auth flow, layout shell, dashboard
This is the first frontend session. No prior frontend code exists.
```

---

## Phase A — Project Scaffold (45-60 min)

### A.1 Create Next.js 14 Project

```powershell
cd F:\Synaptix
npx create-next-app@14 frontend-web --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
cd frontend-web
```

### A.2 Install Dependencies

```powershell
# UI components
npx shadcn@latest init
# Select: New York style, Zinc base color, CSS variables: yes

# Install core shadcn components
npx shadcn@latest add button card input label form toast
npx shadcn@latest add sidebar navigation-menu dropdown-menu avatar badge
npx shadcn@latest add table dialog sheet separator skeleton

# API + state
npm install axios
npm install zustand               # lightweight state management
npm install @tanstack/react-query  # server state + caching

# Auth
npm install jose                   # JWT decode (client-side only, not verification)

# Icons
npm install lucide-react           # already included with shadcn

# Forms
npm install react-hook-form zod @hookform/resolvers
```

### A.3 Project Structure

```
frontend-web/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # Redirect to /login or /dashboard
│   │   ├── login/
│   │   │   └── page.tsx            # Login page
│   │   ├── (authenticated)/        # Route group requiring auth
│   │   │   ├── layout.tsx          # Sidebar + header layout
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx        # Role-specific dashboard
│   │   │   ├── attendance/
│   │   │   │   └── page.tsx        # Placeholder
│   │   │   ├── logbook/
│   │   │   │   └── page.tsx        # Placeholder
│   │   │   ├── electives/
│   │   │   │   └── page.tsx        # Placeholder
│   │   │   └── settings/
│   │   │       └── page.tsx        # Placeholder
│   │   └── api/                    # (empty — we call FastAPI directly)
│   ├── components/
│   │   ├── ui/                     # shadcn components (auto-generated)
│   │   ├── layout/
│   │   │   ├── app-sidebar.tsx     # Main sidebar navigation
│   │   │   ├── header.tsx          # Top header with user menu
│   │   │   └── breadcrumbs.tsx     # Page breadcrumbs
│   │   └── auth/
│   │       ├── login-form.tsx      # Login form component
│   │       └── auth-guard.tsx      # Client-side auth check
│   ├── lib/
│   │   ├── api.ts                  # Axios instance with JWT interceptor
│   │   ├── auth.ts                 # Auth utilities (login, logout, token management)
│   │   └── utils.ts                # shadcn utility (cn function)
│   ├── stores/
│   │   └── auth-store.ts           # Zustand auth state
│   └── types/
│       ├── auth.ts                 # User, LoginRequest, LoginResponse
│       └── api.ts                  # API response envelope types
├── .env.local                      # API_URL=http://localhost:8001
├── next.config.js
├── tailwind.config.ts
└── tsconfig.json
```

### A.4 Environment Configuration

Create `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_APP_NAME=Synaptix
```

Create `.env.example` (committed to git):
```
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_APP_NAME=Synaptix
```

---

## Phase B — API Client + Auth (60-90 min)

### B.1 API Client with JWT Interceptor

```typescript
// src/lib/api.ts
import axios from "axios";
import { useAuthStore } from "@/stores/auth-store";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 → logout
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

### B.2 Auth Store (Zustand)

```typescript
// src/stores/auth-store.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { decodeJwt } from "jose";

interface User {
  id: string;
  tenant_id: string;
  email: string;
  name: string;
  role: "admin" | "faculty" | "hod" | "student" | "super_admin";
  student_id?: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      setAuth: (token: string) => {
        const payload = decodeJwt(token) as Record<string, unknown>;
        const user: User = {
          id: payload.sub as string,
          tenant_id: payload.tenant_id as string,
          email: payload.email as string,
          name: payload.name as string,
          role: payload.role as User["role"],
          student_id: payload.student_id as string | undefined,
        };
        set({ token, user, isAuthenticated: true });
      },

      logout: () => {
        set({ token: null, user: null, isAuthenticated: false });
      },
    }),
    { name: "synaptix-auth" }
  )
);
```

### B.3 Auth Utilities

```typescript
// src/lib/auth.ts
import api from "./api";
import { useAuthStore } from "@/stores/auth-store";

export async function login(email: string, password: string): Promise<void> {
  const response = await api.post("/auth/login", { email, password });
  const { access_token } = response.data;
  useAuthStore.getState().setAuth(access_token);
}

export function logout(): void {
  useAuthStore.getState().logout();
}
```

### B.4 Auth Guard Component

```typescript
// src/components/auth/auth-guard.tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  return <>{children}</>;
}
```

### B.5 Login Page

```typescript
// src/app/login/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/auth";
import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin(email: string, password: string) {
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
      <div className="w-full max-w-md space-y-8 px-4">
        {/* Logo / Branding */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Synaptix</h1>
          <p className="text-sm text-muted-foreground">
            Academic Operations & Intelligence Platform
          </p>
        </div>

        {/* Login Form */}
        <LoginForm onSubmit={handleLogin} error={error} loading={loading} />

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground">
          JMN Medical College &middot; NMC CBME Compliant
        </p>
      </div>
    </div>
  );
}
```

```typescript
// src/components/auth/login-form.tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type LoginValues = z.infer<typeof loginSchema>;

interface LoginFormProps {
  onSubmit: (email: string, password: string) => Promise<void>;
  error: string | null;
  loading: boolean;
}

export function LoginForm({ onSubmit, error, loading }: LoginFormProps) {
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  async function handleSubmit(values: LoginValues) {
    await onSubmit(values.email, values.password);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-center">Sign in</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="faculty@jmn.edu.in"
              {...form.register("email")}
            />
            {form.formState.errors.email && (
              <p className="text-sm text-destructive">
                {form.formState.errors.email.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              {...form.register("password")}
            />
            {form.formState.errors.password && (
              <p className="text-sm text-destructive">
                {form.formState.errors.password.message}
              </p>
            )}
          </div>

          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
```

---

## Phase C — Layout Shell (60-90 min)

### C.1 Authenticated Layout with Sidebar

```typescript
// src/app/(authenticated)/layout.tsx
"use client";

import { AuthGuard } from "@/components/auth/auth-guard";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { Header } from "@/components/layout/header";
import { SidebarProvider } from "@/components/ui/sidebar";

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <SidebarProvider>
        <div className="flex min-h-screen w-full">
          <AppSidebar />
          <div className="flex flex-1 flex-col">
            <Header />
            <main className="flex-1 p-6">{children}</main>
          </div>
        </div>
      </SidebarProvider>
    </AuthGuard>
  );
}
```

### C.2 Sidebar Navigation (Role-Based)

```typescript
// src/components/layout/app-sidebar.tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupLabel,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem,
  SidebarHeader, SidebarFooter,
} from "@/components/ui/sidebar";
import {
  LayoutDashboard, CalendarCheck, BookOpen, GraduationCap,
  FileText, ClipboardList, Users, Settings, Stethoscope,
  LogOut, UserCircle,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { cn } from "@/lib/utils";

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
                  asChild
                  isActive={pathname === item.href}
                >
                  <Link href={item.href} className="flex items-center gap-3">
                    <item.icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Link>
                </SidebarMenuButton>
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
            onClick={() => { logout(); window.location.href = "/login"; }}
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
```

### C.3 Header

```typescript
// src/components/layout/header.tsx
"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { Breadcrumbs } from "./breadcrumbs";

export function Header() {
  return (
    <header className="flex h-14 items-center gap-4 border-b bg-background px-6">
      <SidebarTrigger />
      <Separator orientation="vertical" className="h-6" />
      <Breadcrumbs />
    </header>
  );
}
```

```typescript
// src/components/layout/breadcrumbs.tsx
"use client";

import { usePathname } from "next/navigation";

export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  return (
    <nav className="flex items-center gap-1.5 text-sm text-muted-foreground">
      {segments.map((segment, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && <span>/</span>}
          <span className={i === segments.length - 1 ? "text-foreground font-medium" : ""}>
            {segment.charAt(0).toUpperCase() + segment.slice(1)}
          </span>
        </span>
      ))}
    </nav>
  );
}
```

---

## Phase D — Dashboard (60-90 min)

### D.1 Role-Specific Dashboard

```typescript
// src/app/(authenticated)/dashboard/page.tsx
"use client";

import { useAuthStore } from "@/stores/auth-store";
import { AdminDashboard } from "./admin-dashboard";
import { FacultyDashboard } from "./faculty-dashboard";
import { StudentDashboard } from "./student-dashboard";

export default function DashboardPage() {
  const { user } = useAuthStore();

  switch (user?.role) {
    case "admin":
    case "super_admin":
      return <AdminDashboard />;
    case "faculty":
    case "hod":
      return <FacultyDashboard />;
    case "student":
      return <StudentDashboard />;
    default:
      return <StudentDashboard />;
  }
}
```

### D.2 Admin Dashboard

```typescript
// src/app/(authenticated)/dashboard/admin-dashboard.tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CalendarCheck, Users, BookOpen, AlertTriangle } from "lucide-react";

export function AdminDashboard() {
  // TODO (Session F2): Replace with real API calls
  const stats = [
    { label: "Total Students", value: "—", icon: Users, color: "text-blue-600" },
    { label: "Today's Attendance", value: "—", icon: CalendarCheck, color: "text-green-600" },
    { label: "Pending Logbook Reviews", value: "—", icon: BookOpen, color: "text-amber-600" },
    { label: "At-Risk Students", value: "—", icon: AlertTriangle, color: "text-red-600" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Institution overview</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Placeholder sections for real data */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Activity feed will appear here in Session F2.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Upcoming Events</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Calendar events will appear here in Session F2.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

### D.3 Faculty Dashboard

```typescript
// src/app/(authenticated)/dashboard/faculty-dashboard.tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CalendarCheck, BookOpen, Stethoscope, Clock } from "lucide-react";

export function FacultyDashboard() {
  const stats = [
    { label: "Today's Classes", value: "—", icon: CalendarCheck, color: "text-blue-600" },
    { label: "Pending Signoffs", value: "—", icon: BookOpen, color: "text-amber-600" },
    { label: "DOAP Assessments Due", value: "—", icon: Stethoscope, color: "text-purple-600" },
    { label: "Leave Requests", value: "—", icon: Clock, color: "text-orange-600" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Faculty Dashboard</h1>
        <p className="text-muted-foreground">Your teaching overview</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Today's Schedule</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Your classes for today will appear here in Session F2.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Logbook Queue</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Student submissions awaiting your review will appear here in Session F4.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

### D.4 Student Dashboard

```typescript
// src/app/(authenticated)/dashboard/student-dashboard.tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CalendarCheck, BookOpen, Stethoscope, GraduationCap } from "lucide-react";

export function StudentDashboard() {
  const stats = [
    { label: "Overall Attendance", value: "—%", icon: CalendarCheck, color: "text-green-600" },
    { label: "Logbook Entries", value: "—", icon: BookOpen, color: "text-blue-600" },
    { label: "DOAP Progress", value: "—", icon: Stethoscope, color: "text-purple-600" },
    { label: "Elective Status", value: "—", icon: GraduationCap, color: "text-amber-600" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">My Dashboard</h1>
        <p className="text-muted-foreground">Your academic overview</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Attendance by Subject</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Your subject-wise attendance will appear here in Session F2.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Logbook Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Your recent logbook entries and signoff status will appear here in Session F4.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

### D.5 Placeholder Pages

Create minimal placeholder pages for each navigation item:

```typescript
// src/app/(authenticated)/attendance/page.tsx
export default function AttendancePage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Attendance</h1>
      <p className="text-muted-foreground">
        Attendance marking and tracking will be implemented in Session F2.
      </p>
    </div>
  );
}
```

Repeat for: `/logbook`, `/doap`, `/electives`, `/leave`, `/admissions`, `/people`, `/settings`, `/department`.

---

## Phase E — Root Layout + Entry Point (15 min)

### E.1 Root Layout

```typescript
// src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { QueryProvider } from "@/components/providers/query-provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Synaptix — Academic Operations Platform",
  description: "NMC CBME compliant academic management for JMN Medical College",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <QueryProvider>
          {children}
          <Toaster />
        </QueryProvider>
      </body>
    </html>
  );
}
```

```typescript
// src/components/providers/query-provider.tsx
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, retry: 1 },
    },
  }));

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
```

### E.2 Root Page (Redirect)

```typescript
// src/app/page.tsx
import { redirect } from "next/navigation";

export default function Home() {
  redirect("/dashboard");
}
```

---

## Phase F — Verification + Handoff (15 min)

### F.1 Run the Frontend

```powershell
cd F:\Synaptix\frontend-web
npm run dev
```

Open `http://localhost:3000` in Chrome. Verify:

- [ ] Login page renders with email/password form and Synaptix branding
- [ ] Entering invalid credentials shows error message
- [ ] (If snx-auth is running) valid credentials redirect to dashboard
- [ ] Dashboard shows role-appropriate cards (admin/faculty/student)
- [ ] Sidebar navigation is role-appropriate
- [ ] Clicking nav items loads placeholder pages
- [ ] Logout button returns to login
- [ ] Direct URL access to `/dashboard` without auth redirects to `/login`
- [ ] Responsive: sidebar collapses on mobile width

**If snx-auth is NOT running:** Test with a mock token. Create a temporary dev login bypass:

```typescript
// Temporary: in login-form.tsx, add a "Dev Login" button that calls:
useAuthStore.getState().setAuth("eyJ...<mock JWT with role=admin>...");
router.push("/dashboard");
```

Remove before committing. Or keep behind `process.env.NODE_ENV === "development"` flag.

### F.2 Screenshot Evidence

Take screenshots of:
1. Login page
2. Admin dashboard
3. Faculty dashboard (switch role)
4. Student dashboard (switch role)
5. Sidebar navigation (expanded)
6. Mobile view (narrow browser)

Save to `docs/screenshots/session-f1/`. These are evidence that UI exists.

### F.3 Update Documentation

- `docs/CHANGELOG.md` — "Session F1: Frontend scaffold, auth, layout, dashboards"
- `docs/HANDOFF_NOTES.md` — update with Session F2 scope (attendance UI)
- `.agent-memory/working/CURRENT_FOCUS.md` — "Frontend track started. Session F2: attendance marking UI"

### F.4 Commit

```powershell
cd F:\Synaptix
git add frontend-web/
git commit -m "feat(frontend): Session F1 — Next.js scaffold with auth, layout, dashboards

- Next.js 14 App Router with TypeScript, Tailwind CSS, shadcn/ui
- JWT auth flow with Zustand store and axios interceptor
- Login page with form validation (react-hook-form + zod)
- Role-based sidebar navigation (admin/faculty/hod/student)
- Three dashboard variants (admin, faculty, student) with stat cards
- Placeholder pages for all navigation items
- AuthGuard component for protected routes
- React Query provider for API state management
- Responsive layout with collapsible sidebar

First visible UI of the project. All data is placeholder — 
real API integration begins in Session F2.
"
```

### F.5 Session End

```
SESSION END — Agent: 03-frontend (Session F1)
Duration: ~X hours

FIRST VISIBLE UI DELIVERED.

Pages created: login + dashboard (3 variants) + 9 placeholder pages
Components created: login-form, auth-guard, app-sidebar, header, breadcrumbs
Libraries integrated: shadcn/ui, zustand, react-query, react-hook-form, zod
Auth flow: JWT login → zustand store → axios interceptor → auth guard

What you can see:
- Login page at http://localhost:3000/login
- Admin dashboard with stat cards
- Faculty dashboard with teaching overview
- Student dashboard with academic overview
- Role-based sidebar navigation
- Responsive mobile layout

All data is placeholder (—). Real API calls begin Session F2.

Next session (F2): Attendance UI — faculty marks attendance, student views percentages
```

---

## What Comes in Session F2

Session F2 replaces the placeholder `—` values with real data from the backend APIs:

- `GET /attendance/student/{id}/summary` → student attendance percentages
- `GET /attendance/event/{id}` → faculty attendance roster
- `POST /attendance/mark` → faculty marks attendance
- `GET /attendance/eligibility/{student_id}/{course_id}` → exam eligibility

The dashboard stat cards come alive. The attendance page becomes functional. That's when it goes from "scaffold" to "working application."

---

*After 14 sessions of backend, you can finally SEE what you've built.*