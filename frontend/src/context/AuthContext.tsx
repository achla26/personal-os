"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { apiFetch, setAccessToken } from "@/lib/api";
import { useRouter } from "next/navigation";

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter(); 

  const checkAuth = async () => {
    try {
      // Try to silently refresh token on page load/refresh
      const data = await apiFetch("/auth/refresh", { method: "POST" });
      if (data && data.access_token) {
        setAccessToken(data.access_token);
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
      }
    } catch {
      setAccessToken(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const logout = async () => {
    try {
      // Call backend to revoke refresh token and clear cookie
      await apiFetch("/auth/logout", { method: "POST" });
    } catch {
      // Continue client cleanup even if network fails
    } finally {
      setAccessToken(null);
      setIsAuthenticated(false);
      router.push("/login");
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}