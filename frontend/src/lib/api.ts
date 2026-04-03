import { AuthResponse, UsageResponse } from "./types";

const API_BASE_URL = "http://localhost:8000/api/v1";

function getToken(): string | null {
  return localStorage.getItem("auth_token");
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> || {})
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    let errorMessage = "Request failed";

    try {
      const error = await response.json();
      errorMessage = error.detail || errorMessage;
    } catch {}

    throw new Error(errorMessage);
  }

  return response.json();
}

export const api = {

  // AUTH
  login: async (email: string, password: string) => {
    const result = await request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });

    if (result.access_token) {
        localStorage.setItem("auth_token", result.access_token);
        localStorage.setItem("user_id", result.user_id);
    }

    return result;
  },

  register: async (email: string, password: string, name: string) => {
    return request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        full_name: name
      })
    });
  },

  logout: () => {
    localStorage.removeItem("auth_token");
  },

  // USAGE
  getUsageData: (userId: string) =>
    request<UsageResponse>(`/usage/user/${userId}/recent`),

  // NEW: TREND DATA
  getTrends: (userId: string) =>
    request(`/usage/user/${userId}/trends`),

  getAnalytics: (userId: string) =>
  request(`/usage/user/${userId}/analytics`),

  submitLaptopData: (data: unknown) =>
    request("/usage/laptop", {
      method: "POST",
      body: JSON.stringify(data)
    }),

  submitMobileData: (data: unknown) =>
    request("/usage/mobile", {
      method: "POST",
      body: JSON.stringify(data)
    }),
};