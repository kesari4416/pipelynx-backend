import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import { authApi, tokenStorage, userStorage } from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(userStorage.get());
  const [loading, setLoading] = useState(true);

  // Verify session on mount
  useEffect(() => {
    const token = tokenStorage.get();
    if (!token) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then((data) => {
        setUser(data);
        userStorage.set(data);
      })
      .catch(() => {
        tokenStorage.clear();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email, password) => {
    const result = await authApi.login({ email, password });
    tokenStorage.set(result.access_token);
    userStorage.set(result.user);
    setUser(result.user);
    return result;
  }, []);

  const register = useCallback(async (data) => {
    const result = await authApi.register(data);
    tokenStorage.set(result.access_token);
    userStorage.set(result.user);
    setUser(result.user);
    return result;
  }, []);

  const logout = useCallback(() => {
    tokenStorage.clear();
    setUser(null);
    window.location.href = "/auth/login";
  }, []);

  // Memoize context value to prevent unnecessary re-renders of consumers
  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
