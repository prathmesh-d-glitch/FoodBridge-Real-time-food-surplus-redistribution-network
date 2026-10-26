export interface UserSession {
  uid: string;
  name: string;
  email: string;
  role: 'donor' | 'ngo' | 'volunteer' | 'admin';
  token: string;
  organization?: string;
  phone?: string;
}

export interface UserAccount extends UserSession {
  password: string;
}

export const TEST_ACCOUNTS: Record<string, UserAccount> = {
  'admin@gmail.com': {
    uid: 'admin_super',
    name: 'FoodBridge Platform Admin',
    email: 'admin@gmail.com',
    password: '1234',
    role: 'admin',
    token: 'token-admin@gmail.com',
    organization: 'FoodBridge Central Administration',
    phone: '+91 98765 43213',
  },
  'donor@gmail.com': {
    uid: 'donor_taj_palace',
    name: 'Taj Palace Luxury Catering',
    email: 'donor@gmail.com',
    password: '1234',
    role: 'donor',
    token: 'token-donor@gmail.com',
    organization: 'Taj Hotels & Banquets',
    phone: '+91 98765 43210',
  },
  'ngo@gmail.com': {
    uid: 'ngo_robin_hood',
    name: 'Robin Hood Army Bangalore',
    email: 'ngo@gmail.com',
    password: '1234',
    role: 'ngo',
    token: 'token-ngo@gmail.com',
    organization: 'Robin Hood Army',
    phone: '+91 98765 43211',
  },
  'volunteer@gmail.com': {
    uid: 'vol_arun_kumar',
    name: 'Arun Kumar',
    email: 'volunteer@gmail.com',
    password: '1234',
    role: 'volunteer',
    token: 'token-volunteer@gmail.com',
    organization: 'Green Courier Volunteers',
    phone: '+91 98765 43212',
  },
};

export const PRESET_USERS: Record<string, UserSession> = {
  admin: TEST_ACCOUNTS['admin@gmail.com'],
  donor: TEST_ACCOUNTS['donor@gmail.com'],
  ngo: TEST_ACCOUNTS['ngo@gmail.com'],
  volunteer: TEST_ACCOUNTS['volunteer@gmail.com'],
};

export const authenticateUser = (email: string, password: string): UserSession => {
  const normalizedEmail = email.trim().toLowerCase();
  const account = TEST_ACCOUNTS[normalizedEmail];

  if (!account) {
    // Check if user is trying one of the previous legacy demo emails
    if (normalizedEmail.includes('admin')) {
      throw new Error("Account not found. For Admin testing, use email 'admin@gmail.com' and password '1234'.");
    }
    throw new Error(
      `No account registered for '${email}'. Test accounts available:\n` +
      `• admin@gmail.com (password: 1234)\n` +
      `• donor@gmail.com (password: 1234)\n` +
      `• ngo@gmail.com (password: 1234)\n` +
      `• volunteer@gmail.com (password: 1234)`
    );
  }

  if (account.password !== password) {
    throw new Error("Invalid password. Test password for all accounts is '1234'.");
  }

  const session: UserSession = {
    uid: account.uid,
    name: account.name,
    email: account.email,
    role: account.role,
    token: account.token,
    organization: account.organization,
    phone: account.phone,
  };

  saveUserSession(session);
  return session;
};

export const getSavedUserSession = (): UserSession | null => {
  const saved = localStorage.getItem('foodbridge_session');
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch {
      // fallback
    }
  }
  // Default to donor session for instant out-of-the-box exploration
  return PRESET_USERS.donor;
};

export const saveUserSession = (session: UserSession): void => {
  localStorage.setItem('foodbridge_session', JSON.stringify(session));
};

export const clearUserSession = (): void => {
  localStorage.removeItem('foodbridge_session');
};
