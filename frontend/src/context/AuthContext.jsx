import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../lib/api';

const AuthContext = createContext();

export const useAuth = () => {
  return useContext(AuthContext);
};

export const AuthProvider = ({ children }) => {
  // Helper to decode token robustly
  const decodeToken = (t) => {
    try {
      const base64Url = t.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      return JSON.parse(jsonPayload);
    } catch (e) {
      return null;
    }
  };

  const [token, setToken] = useState(() => localStorage.getItem('token') || null);
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('token');
    if (stored) {
      const payload = decodeToken(stored);
      if (payload) return { email: payload.sub };
    }
    return null;
  });

  // Sync token changes to localStorage and derive User
  const updateAuth = (newToken) => {
    if (newToken) {
      const payload = decodeToken(newToken);
      if (payload) {
        setUser({ email: payload.sub });
        setToken(newToken);
        localStorage.setItem('token', newToken);
        return;
      }
    }
    // Logout / Clear state
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  };

  const login = async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email); // OAuth2 expects 'username' instead of 'email'
    formData.append('password', password);

    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    updateAuth(response.data.access_token);
    return response.data;
  };

  const register = async (email, password) => {
    const response = await api.post('/auth/register', { email, password });
    updateAuth(response.data.access_token);
    return response.data;
  };

  const logout = () => {
    updateAuth(null);
  };

  const value = {
    user,
    token,
    isAuthenticated: !!user,
    login,
    register,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
