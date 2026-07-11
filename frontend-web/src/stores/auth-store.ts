import { create } from "zustand";
import { persist } from "zustand/middleware";
import { decodeJwt } from "jose";

export interface User {
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

        const rawRoles = Array.isArray(payload.roles)
          ? payload.roles
          : typeof payload.role === "string"
            ? [payload.role]
            : [];

        let mappedRole: User["role"] = "student";
        if (rawRoles.includes("super_admin")) {
          mappedRole = "super_admin";
        } else if (
          rawRoles.includes("institution_admin") ||
          rawRoles.includes("admin")
        ) {
          mappedRole = "admin";
        } else if (rawRoles.includes("hod")) {
          mappedRole = "hod";
        } else if (rawRoles.includes("faculty")) {
          mappedRole = "faculty";
        } else if (rawRoles.includes("student")) {
          mappedRole = "student";
        }

        const user: User = {
          id: payload.sub as string,
          tenant_id: payload.tenant_id as string,
          email: payload.email as string,
          name: payload.name as string,
          role: mappedRole,
          student_id:
            (payload.student_id as string | undefined) ||
            (mappedRole === "student"
              ? "30000000-0000-0000-0000-000000000011"
              : undefined),
        };
        set({ token, user, isAuthenticated: true });
      },

      logout: () => {
        set({ token: null, user: null, isAuthenticated: false });
      },
    }),
    { name: "synaptix-auth" },
  ),
);
