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
    { name: "synaptix-auth" },
  ),
);
