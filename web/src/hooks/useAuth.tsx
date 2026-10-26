import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  authenticateUser,
  clearUserSession,
  getSavedUserSession,
  PRESET_USERS,
  saveUserSession,
  UserSession,
} from '../firebase';

export interface AuthContextType {
  user: UserSession | null;
  setUser: (user: UserSession | null) => void;
  login: (email: string, password: string) => UserSession;
  loginWithPreset: (email: string) => UserSession;
  logout: () => void;
  switchRole: (role: 'donor' | 'ngo' | 'volunteer' | 'admin') => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserSession | null>(() => getSavedUserSession());

  useEffect(() => {
    const handleStorageChange = () => {
      setUser(getSavedUserSession());
    };
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const login = (email: string, password: string): UserSession => {
    const session = authenticateUser(email, password);
    setUser(session);
    saveUserSession(session);
    return session;
  };

  const loginWithPreset = (email: string): UserSession => {
    return login(email, '1234');
  };

  const logout = () => {
    clearUserSession();
    setUser(null);
  };

  const switchRole = (role: 'donor' | 'ngo' | 'volunteer' | 'admin') => {
    const newSession = PRESET_USERS[role];
    if (newSession) {
      setUser(newSession);
      saveUserSession(newSession);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        login,
        loginWithPreset,
        logout,
        switchRole,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
