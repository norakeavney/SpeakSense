'use client';

import { createContext, useContext, useState, useEffect } from 'react';
import { isAuthenticated, getUserProfile, logout as apiLogout } from '../lib/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined' || typeof document === 'undefined') {
      return;
    }

    try {
      const rawSettings = localStorage.getItem('speaksense_settings');
      if (!rawSettings) {
        document.documentElement.classList.remove('dark');
        return;
      }

      const parsedSettings = JSON.parse(rawSettings);
      document.documentElement.classList.toggle('dark', parsedSettings?.theme === 'dark');
    } catch (error) {
      document.documentElement.classList.remove('dark');
    }
  }, []);

  const checkAuthStatus = async () => {
    try {
      if (isAuthenticated()) {
        const profile = await getUserProfile();
        setUser(profile);
        setIsLoggedIn(true);
      }
    } catch (error) {
      // Clear invalid tokens on auth failure
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = (userData) => {
    setUser(userData);
    setIsLoggedIn(true);
  };

  const logout = async () => {
    try {
      await apiLogout();
    } catch (error) {
      // Logout error handled silently
    } finally {
      setUser(null);
      setIsLoggedIn(false);
    }
  };

  const value = {
    user,
    isLoggedIn,
    loading,
    login,
    logout,
    checkAuthStatus,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};