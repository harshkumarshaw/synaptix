import axios from "axios";
import { useAuthStore } from "@/stores/auth-store";

const AUTH_URL = process.env.NEXT_PUBLIC_AUTH_URL || "http://localhost:8001";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";
const LOGBOOK_URL =
  process.env.NEXT_PUBLIC_LOGBOOK_URL || "http://localhost:8006";
const INSTITUTION_URL =
  process.env.NEXT_PUBLIC_INSTITUTION_URL || "http://localhost:8007";
const WORKFLOW_URL =
  process.env.NEXT_PUBLIC_WORKFLOW_URL || "http://localhost:8010";

const api = axios.create({
  headers: { "Content-Type": "application/json" },
});

// Attach JWT and dynamically set baseURL and prefix based on request path
api.interceptors.request.use((config) => {
  config.headers["X-Tenant-ID"] = "00000000-0000-0000-0000-000000000001";
  const url = config.url || "";
  if (url.startsWith("/auth") || url.startsWith("/api/v1/auth")) {
    config.baseURL = AUTH_URL;
  } else if (
    url.startsWith("/attendance") ||
    url.startsWith("/events") ||
    url.startsWith("/leave")
  ) {
    config.baseURL = API_URL;
  } else if (
    url.startsWith("/electives") ||
    url.startsWith("/doap") ||
    url.startsWith("/logbook")
  ) {
    config.baseURL = LOGBOOK_URL;
  } else if (
    url.startsWith("/institutions") ||
    url.startsWith("/campus") ||
    url.startsWith("/departments")
  ) {
    config.baseURL = INSTITUTION_URL;
  } else if (url.startsWith("/workflow")) {
    config.baseURL = WORKFLOW_URL;
  } else {
    config.baseURL = API_URL; // fallback to Academic service
  }

  // Prepend /api/v1 if not already present
  if (url && !url.startsWith("/api/v1") && !url.startsWith("http")) {
    config.url = `/api/v1${url}`;
  }

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
      const isLoginRequest = error.config?.url?.includes("/auth/login");
      useAuthStore.getState().logout();
      if (typeof window !== "undefined" && !isLoginRequest) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export default api;
