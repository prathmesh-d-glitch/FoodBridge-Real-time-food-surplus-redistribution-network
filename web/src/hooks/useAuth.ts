import { useState } from 'react';
import { getSavedUserSession, PRESET_USERS, saveUserSession, UserSession } from '../firebase';

export function useAuth() {
  const [user, setUser] = useState<UserSession>(getSavedUserSession);

  const switchRole = (role: 'donor' | 'ngo' | 'volunteer' | 'admin') => {
    const newSession = PRESET_USERS[role];
    if (newSession) {
      setUser(newSession);
      saveUserSession(newSession);
    }
  };

  return {
    user,
    switchRole,
    isAuthenticated: !!user,
  };
}
