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
