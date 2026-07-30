import { AuthResponse, UsageResponse } from "./types";

const API_BASE_URL =
  "https://digital-fatigue-prediction-system.onrender.com/api/v1";

let refreshInFlight: Promise<AuthResponse | null> | null = null;

function getToken(): string | null {
  return localStorage.getItem("auth_token");
}

function getRefreshToken(): string | null {
  return localStorage.getItem("auth_refresh_token");
}

function clearAuthState() {
  localStorage.removeItem("auth_token");
  localStorage.removeItem("auth_refresh_token");
  localStorage.removeItem("auth_user");
  localStorage.removeItem("user_id");
  globalThis.dispatchEvent(new Event("auth:invalidated"));
}

function toHeaderRecord(headers?: HeadersInit): Record<string, string> {
  return Object.fromEntries(new Headers(headers).entries());
}

function buildRequestHeaders(token: string | null, headers?: HeadersInit): Record<string, string> {
  const requestHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...toHeaderRecord(headers),
  };

  if (token) {
    requestHeaders.Authorization = `Bearer ${token}`;
  }

  return requestHeaders;
}

async function readErrorMessage(response: Response): Promise<string> {
  let errorMessage = "Request failed";

  try {
    const error = await response.json();
    errorMessage = error.detail || errorMessage;
  } catch {}

  return errorMessage;
}

function shouldTryRefresh(endpoint: string): boolean {
  return endpoint !== "/auth/login" && endpoint !== "/auth/register" && endpoint !== "/auth/refresh";
}

function persistAuthTokens(result: AuthResponse) {
  if (result.access_token) {
    localStorage.setItem("auth_token", result.access_token);
  }

  if (result.refresh_token) {
    localStorage.setItem("auth_refresh_token", result.refresh_token);
  }

  if (result.user_id) {
    localStorage.setItem("user_id", result.user_id);
  } else if (result.access_token) {
    try {
      const payload = JSON.parse(atob(result.access_token.split(".")[1]));
      if (payload?.user_id) {
        localStorage.setItem("user_id", payload.user_id);
      }
    } catch {}
  }
}

async function refreshAuthSession(): Promise<AuthResponse | null> {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    return null;
  }

  const result = (await response.json()) as AuthResponse;
  persistAuthTokens(result);
  return result;
}

async function refreshAuthSessionOnce(): Promise<AuthResponse | null> {
  if (!refreshInFlight) {
    refreshInFlight = refreshAuthSession().finally(() => {
      refreshInFlight = null;
    });
  }

  return refreshInFlight;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();

  const headers = buildRequestHeaders(token, options.headers);

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers
  });

  if (response.status === 401 && shouldTryRefresh(endpoint)) {
    const renewed = await refreshAuthSessionOnce();

    if (renewed?.access_token) {
      const retryHeaders = buildRequestHeaders(renewed.access_token, options.headers);

      const retryResponse = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: retryHeaders,
      });

      if (retryResponse.ok) {
        return retryResponse.json();
      }

      if (retryResponse.status === 401) {
        clearAuthState();
      }

      throw new Error(await readErrorMessage(retryResponse));
    }
  }

  if (!response.ok) {
    const errorMessage = await readErrorMessage(response);

    if (response.status === 401) {
      clearAuthState();
    }

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

    persistAuthTokens(result);

    return result;
  },

  register: async (email: string, password: string, name: string) => {
    const result = await request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        full_name: name
      })
    });

    persistAuthTokens(result);

    return result;
  },

  refreshSession: async () => {
    const result = await refreshAuthSession();
    return result;
  },

  logout: () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_refresh_token");
    localStorage.removeItem("auth_user");
    localStorage.removeItem("user_id");
  },

  // USAGE
  getUsageData: (userId: string) =>
    request<UsageResponse>(`/usage/user/${userId}/recent`),

  // NEW: TREND DATA
  getTrends: (userId: string, days: number = 7, offsetDays: number = 0) =>
    request(`/usage/user/${userId}/trends?days=${days}&offset_days=${offsetDays}`),

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

  // PREFERENCES
  getPreferences: () =>
    request("/users/me/preferences", { method: "GET" }),

  updatePreferences: (preferences: unknown) =>
    request("/users/me/preferences", {
      method: "PUT",
      body: JSON.stringify(preferences)
    }),

  // GOALS
  getGoals: () =>
    request("/users/me/goals", { method: "GET" }),

  updateGoals: (goals: unknown) =>
    request("/users/me/goals", {
      method: "PUT",
      body: JSON.stringify(goals)
    }),

  // NOTIFICATIONS
  getNotifications: (limit: number = 20, unreadOnly: boolean = false) =>
    request(`/users/me/notifications?limit=${limit}&unread_only=${unreadOnly}`, {
      method: "GET"
    }),

  getUnreadCount: () =>
    request("/users/me/notifications/unread-count", { method: "GET" }),

  markNotificationAsRead: (notificationId: string) =>
    request(`/users/me/notifications/${notificationId}/read`, { method: "PUT" }),

  markAllNotificationsAsRead: () =>
    request("/users/me/notifications/read-all", { method: "PUT" }),

  deleteNotification: (notificationId: string) =>
    request(`/users/me/notifications/${notificationId}`, { method: "DELETE" }),

  deleteAllNotifications: () =>
    request("/users/me/notifications", { method: "DELETE" }),

  createNotification: (notification: unknown) =>
    request("/users/me/notifications", {
      method: "POST",
      body: JSON.stringify(notification)
    }),
  // ACTIVITY LOGGING (web)
  logActivity: (userId: string, events: any[]) =>
    request(`/usage/user/${userId}/activity`, {
      method: "POST",
      body: JSON.stringify({ events }),
    }),
};