import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { User } from "@/lib/types";
import { api } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
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

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem("auth_token");
    const savedUser = localStorage.getItem("auth_user");

    const parsedUser = safeParse(savedUser);

    if (savedToken && parsedUser) {
      setToken(savedToken);
      setUser(parsedUser);
    }

    setIsLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.login(email, password);

    const token = res.access_token;

    let userData: User | null = res.user ?? null;

    // If backend didn't send user object, decode token
    if (!userData && token) {
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        userData = {
          id: payload.user_id,
          email: payload.sub,
          full_name: payload.sub,
        } as User;
      } catch {
        userData = null;
      }
    }

    if (token) {
      localStorage.setItem("auth_token", token);
      setToken(token);
    }

    if (userData) {
      localStorage.setItem("auth_user", JSON.stringify(userData));
      setUser(userData);
    }
  }, []);

  const register = useCallback(async (email: string, password: string, name: string) => {
    const res = await api.register(email, password, name);

    const token = res.access_token;

    let userData: User | null = res.user ?? null;

    if (!userData && token) {
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        userData = {
          id: payload.user_id,
          email: payload.sub,
          full_name: name,
        } as User;
      } catch {
        userData = null;
      }
    }

    if (token) {
      localStorage.setItem("auth_token", token);
      setToken(token);
    }

    if (userData) {
      localStorage.setItem("auth_user", JSON.stringify(userData));
      setUser(userData);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}