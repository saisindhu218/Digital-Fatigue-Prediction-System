import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import { User } from "@/lib/types";
import { api } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  updateProfile: (updates: { name?: string }) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Safe JSON parser
function safeParse(value: string | null) {
  if (!value || value === "undefined") return null;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function isValidJwtToken(token: string | null): boolean {
  if (!token || token === "undefined" || token === "demo_token") return false;

  const parts = token.split(".");
  if (parts.length !== 3) return false;

  try {
    const payload = JSON.parse(atob(parts[1]));
    if (!payload?.sub || !payload?.user_id) return false;

    if (typeof payload.exp === "number") {
      const nowInSeconds = Math.floor(Date.now() / 1000);
      if (payload.exp <= nowInSeconds) return false;
    }

    return true;
  } catch {
    return false;
  }
}

function decodeUserFromToken(token: string | null, fallbackName?: string): User | null {
  if (!token) return null;

  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    if (!payload?.user_id || !payload?.sub) return null;

    return {
      id: payload.user_id,
      email: payload.sub,
      name: fallbackName || payload.sub.split("@")[0],
    } as User;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem("auth_token");
    const savedRefreshToken = localStorage.getItem("auth_refresh_token");
    const savedUser = localStorage.getItem("auth_user");

    const parsedUser = safeParse(savedUser);

    const bootstrapSession = async () => {
      if (isValidJwtToken(savedToken) && parsedUser) {
        setToken(savedToken);
        setUser(parsedUser);
        setIsLoading(false);
        return;
      }

      if (savedRefreshToken) {
        const refreshed = await api.refreshSession();
        if (refreshed?.access_token) {
          setToken(refreshed.access_token);
          setUser(parsedUser || decodeUserFromToken(refreshed.access_token));
          setIsLoading(false);
          return;
        }
      }

      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_refresh_token");
      localStorage.removeItem("auth_user");
      localStorage.removeItem("user_id");
      setIsLoading(false);
    };

    void bootstrapSession();
  }, []);

  useEffect(() => {
    const handleInvalidation = () => {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_refresh_token");
      localStorage.removeItem("auth_user");
      localStorage.removeItem("user_id");
      setToken(null);
      setUser(null);
    };

    globalThis.addEventListener("auth:invalidated", handleInvalidation);
    return () => globalThis.removeEventListener("auth:invalidated", handleInvalidation);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.login(email, password);

    const token = res.access_token;

    // Decode token to get user data since API doesn't return user object
    const userData = decodeUserFromToken(token);

    if (token) {
      localStorage.setItem("auth_token", token);
      setToken(token);
    }

    if (res.refresh_token) {
      localStorage.setItem("auth_refresh_token", res.refresh_token);
    }

    if (userData) {
      localStorage.setItem("auth_user", JSON.stringify(userData));
      setUser(userData);
    }
  }, []);

  const register = useCallback(async (email: string, password: string, name: string) => {
    const res = await api.register(email, password, name);

    const token = res.access_token;

    // Decode token to get user data since API doesn't return user object
    const userData = decodeUserFromToken(token, name);

    if (token) {
      localStorage.setItem("auth_token", token);
      setToken(token);
    }

    if (res.refresh_token) {
      localStorage.setItem("auth_refresh_token", res.refresh_token);
    }

    if (userData) {
      localStorage.setItem("auth_user", JSON.stringify(userData));
      setUser(userData);
    }
  }, []);

  const updateProfile = useCallback((updates: { name?: string }) => {
    setUser((prev) => {
      if (!prev) return prev;

      const updatedUser: User = {
        ...prev,
        ...updates,
      };

      localStorage.setItem("auth_user", JSON.stringify(updatedUser));
      return updatedUser;
    });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_refresh_token");
    localStorage.removeItem("auth_user");
    localStorage.removeItem("user_id");
    setToken(null);
    setUser(null);
  }, []);

  const contextValue = useMemo(() => ({
    user,
    token,
    isAuthenticated: !!token,
    isLoading,
    login,
    register,
    updateProfile,
    logout,
  }), [user, token, isLoading, login, register, updateProfile, logout]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}