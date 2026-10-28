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
  // ── Administrator ──
  'admin@gmail.com': {
    uid: 'admin_super',
    name: 'FoodBridge Central Admin [System Administrator - Admin]',
    email: 'admin@gmail.com',
    password: '1234',
    role: 'admin',
    token: 'token-admin@gmail.com',
    organization: 'FoodBridge Platform Administration',
    phone: '+91 98765 43213',
  },

  // ── Donors / Caterers ──
  'donor@gmail.com': {
    uid: 'donor_taj_palace',
    name: 'Taj Palace Luxury Catering [Taj Palace - Donor]',
    email: 'donor@gmail.com',
    password: '1234',
    role: 'donor',
    token: 'token-donor@gmail.com',
    organization: 'Taj Hotels & Banquets',
    phone: '+91 98765 43210',
  },
  'grand@banquets.com': {
    uid: 'donor_grand_banquet',
    name: 'Grand Convention & Banquets [Grand Banquets - Donor]',
    email: 'grand@banquets.com',
    password: '1234',
    role: 'donor',
    token: 'mock:donor:donor_grand_banquet:Grand Convention & Banquets',
    organization: 'Grand Convention Center Koramangala',
    phone: '+91 98765 43216',
  },
  'itc@gardenia.com': {
    uid: 'donor_itc_gardenia',
    name: 'ITC Gardenia Banquets [ITC Gardenia - Donor]',
    email: 'itc@gardenia.com',
    password: '1234',
    role: 'donor',
    token: 'mock:donor:donor_itc_gardenia:ITC Gardenia Banquets',
    organization: 'ITC Luxury Collection',
    phone: '+91 98765 43217',
  },

  // ── NGOs / Food Banks / Shelters ──
  'ngo@gmail.com': {
    uid: 'ngo_robin_hood',
    name: 'Robin Hood Army Bangalore [Robin Hood Army - NGO]',
    email: 'ngo@gmail.com',
    password: '1234',
    role: 'ngo',
    token: 'token-ngo@gmail.com',
    organization: 'Robin Hood Army Indiranagar',
    phone: '+91 98765 43211',
  },
  'kitchen@koramangala.org': {
    uid: 'ngo_koramangala',
    name: 'Koramangala Community Kitchen [Koramangala Kitchen - NGO]',
    email: 'kitchen@koramangala.org',
    password: '1234',
    role: 'ngo',
    token: 'mock:ngo:ngo_koramangala:Koramangala Community Kitchen',
    organization: 'Koramangala Food Bank Trust',
    phone: '+91 98765 43215',
  },
  'hasiru@feeding.org': {
    uid: 'ngo_hasiru_dala',
    name: 'Hasiru Dala Feeding Centre [Hasiru Dala - NGO]',
    email: 'hasiru@feeding.org',
    password: '1234',
    role: 'ngo',
    token: 'mock:ngo:ngo_hasiru_dala:Hasiru Dala Feeding Centre',
    organization: 'Hasiru Dala Wastepickers Trust',
    phone: '+91 98765 43218',
  },

  // ── Volunteer Couriers ──
  'volunteer@gmail.com': {
    uid: 'vol_arun_kumar',
    name: 'Arun Kumar [Arun Kumar - Volunteer]',
    email: 'volunteer@gmail.com',
    password: '1234',
    role: 'volunteer',
    token: 'token-volunteer@gmail.com',
    organization: 'Green Courier Volunteers',
    phone: '+91 98765 43212',
  },
  'priya@courier.org': {
    uid: 'vol_priya_sharma',
    name: 'Priya Sharma [Priya Sharma - Volunteer]',
    email: 'priya@courier.org',
    password: '1234',
    role: 'volunteer',
    token: 'mock:volunteer:vol_priya_sharma:Priya Sharma',
    organization: 'Rapid Relief Couriers',
    phone: '+91 98765 43219',
  },
};

export const PRESET_USERS: Record<string, UserSession> = {
  admin: TEST_ACCOUNTS['admin@gmail.com'],
  donor: TEST_ACCOUNTS['donor@gmail.com'],
  'donor_grand': TEST_ACCOUNTS['grand@banquets.com'],
  'donor_itc': TEST_ACCOUNTS['itc@gardenia.com'],
  ngo: TEST_ACCOUNTS['ngo@gmail.com'],
  'ngo_koramangala': TEST_ACCOUNTS['kitchen@koramangala.org'],
  'ngo_hasiru': TEST_ACCOUNTS['hasiru@feeding.org'],
  volunteer: TEST_ACCOUNTS['volunteer@gmail.com'],
  'volunteer_priya': TEST_ACCOUNTS['priya@courier.org'],
};

export const authenticateUser = (email: string, password: string): UserSession => {
  const normalizedEmail = email.trim().toLowerCase();

  // 1. Check pre-configured test accounts
  let account = TEST_ACCOUNTS[normalizedEmail];

  // 2. Check dynamically registered partner applications
  if (!account) {
    try {
      const dynamicPartners = JSON.parse(localStorage.getItem('foodbridge_registered_partners') || '{}');
      const adminVers = JSON.parse(localStorage.getItem('foodbridge_admin_verifications') || '[]');

      if (dynamicPartners[normalizedEmail]) {
        const dp = dynamicPartners[normalizedEmail];
        
        // Check if Admin has approved their verification
        const verRecord = adminVers.find((v: any) => 
          (v.email && v.email.toLowerCase() === normalizedEmail) || 
          (v.name && dp.name && v.name.toLowerCase() === dp.name.toLowerCase())
        );
        const isApproved = dp.status === 'verified' || verRecord?.status === 'verified';

        if (!isApproved) {
          throw new Error(
            `Account '${dp.name}' is currently PENDING Admin Verification. ` +
            `Please log in as Admin (admin@gmail.com) -> Admin Console -> click 'Approve' to activate this partner.`
          );
        }

        account = {
          uid: dp.uid || `user_${Date.now()}`,
          name: `${dp.name} [${dp.name} - ${dp.type.toUpperCase()}]`,
          email: normalizedEmail,
          password: dp.password || verRecord?.password || '1234',
          role: dp.type as any,
          token: `mock:${dp.type}:${dp.uid || 'dynamic_user'}:${dp.name}`,
          organization: dp.name,
          phone: dp.phone || '+91 98765 00000',
        };
      } else {
        // Fallback: Check if this user exists in admin verifications list directly
        const verRecord = adminVers.find((v: any) => v.email && v.email.toLowerCase() === normalizedEmail);
        if (verRecord) {
          if (verRecord.status !== 'verified') {
            throw new Error(
              `Account '${verRecord.name}' is currently PENDING Admin Verification. ` +
              `Please log in as Admin (admin@gmail.com) -> Admin Console -> click 'Approve' to activate this partner.`
            );
          }

          account = {
            uid: verRecord.id || `user_${Date.now()}`,
            name: `${verRecord.name} [${verRecord.name} - ${(verRecord.type || 'donor').toUpperCase()}]`,
            email: normalizedEmail,
            password: verRecord.password || '1234',
            role: (verRecord.type || 'donor') as any,
            token: `mock:${verRecord.type || 'donor'}:${verRecord.id || 'dynamic_user'}:${verRecord.name}`,
            organization: verRecord.name,
            phone: verRecord.phone || '+91 98765 00000',
          };
        }
      }
    } catch (e: any) {
      if (e.message && e.message.includes('PENDING Admin Verification')) {
        throw e;
      }
    }
  }

  if (!account) {
    throw new Error(
      `No account registered for '${email}'. Try one of the pre-configured accounts:\n` +
      `• donor@gmail.com [Taj Palace - Donor]\n` +
      `• grand@banquets.com [Grand Banquets - Donor]\n` +
      `• itc@gardenia.com [ITC Gardenia - Donor]\n` +
      `• ngo@gmail.com [Robin Hood Army - NGO]\n` +
      `• kitchen@koramangala.org [Koramangala Kitchen - NGO]\n` +
      `• hasiru@feeding.org [Hasiru Dala - NGO]\n` +
      `• volunteer@gmail.com [Arun Kumar - Volunteer]\n` +
      `• priya@courier.org [Priya Sharma - Volunteer]\n` +
      `• admin@gmail.com [System Administrator - Admin]\n` +
      `Or apply as a new Partner using the tab above.`
    );
  }

  if (account.password !== password) {
    if (account.password === '1234') {
      throw new Error("Invalid password. Test password for pre-configured accounts is '1234'.");
    } else {
      throw new Error(`Invalid password for '${email}'. Please enter your registered account password.`);
    }
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
