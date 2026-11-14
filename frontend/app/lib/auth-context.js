"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { getCurrentUser, logIn, logOut } from "./auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState("loading");

  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setStatus("authenticated");
      return currentUser;
    } catch (error) {
      if (error.status === 401) {
        setUser(null);
        setStatus("anonymous");
        return null;
      }
      setStatus("error");
      throw error;
    }
  }, []);

  useEffect(() => {
    let active = true;
    getCurrentUser()
      .then((currentUser) => {
        if (active) {
          setUser(currentUser);
          setStatus("authenticated");
        }
      })
      .catch((error) => {
        if (!active) return;
        setUser(null);
        setStatus(error.status === 401 ? "anonymous" : "error");
      });
    return () => {
      active = false;
    };
  }, []);

  const value = useMemo(
    () => ({
      user,
      status,
      refreshUser,
      async signIn(credentials) {
        const authenticatedUser = await logIn(credentials);
        setUser(authenticatedUser);
        setStatus("authenticated");
        return authenticatedUser;
      },
      async signOut() {
        await logOut();
        setUser(null);
        setStatus("anonymous");
      },
      clearSession() {
        setUser(null);
        setStatus("anonymous");
      },
    }),
    [user, status, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
