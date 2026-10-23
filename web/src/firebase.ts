export interface UserSession {
  uid: string;
  name: string;
  email: string;
  role: 'donor' | 'ngo' | 'volunteer' | 'admin';
  token: string;
}

export const PRESET_USERS: Record<string, UserSession> = {
  donor: {
    uid: 'donor_taj_palace',
    name: 'Taj Palace Luxury Catering',
    email: 'chef@tajpalace.example',
    role: 'donor',
    token: 'mock-donor-token',
  },
  ngo: {
    uid: 'ngo_robin_hood',
    name: 'Robin Hood Army Bangalore',
    email: 'ops@robinhoodarmy.example',
    role: 'ngo',
    token: 'mock-ngo-token',
  },
  volunteer: {
    uid: 'vol_arun_kumar',
    name: 'Arun Kumar',
    email: 'arun.k@volunteer.example',
    role: 'volunteer',
    token: 'mock-volunteer-token',
  },
  admin: {
    uid: 'admin_super',
    name: 'FoodBridge Platform Admin',
    email: 'admin@foodbridge.org',
    role: 'admin',
    token: 'mock-admin-token',
  },
};

export const getSavedUserSession = (): UserSession => {
  const saved = localStorage.getItem('foodbridge_session');
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch {
      // fallback
    }
  }
  return PRESET_USERS.donor;
};

export const saveUserSession = (session: UserSession): void => {
  localStorage.setItem('foodbridge_session', JSON.stringify(session));
};
