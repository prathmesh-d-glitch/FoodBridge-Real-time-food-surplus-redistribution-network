import React, { useState } from 'react';
import {
  Shield,
  Utensils,
  HeartHandshake,
  Truck,
  Mail,
  Lock,
  ArrowRight,
  AlertCircle,
  Eye,
  EyeOff,
  CheckCircle2,
  Sparkles,
  MapPin,
  Building2,
  FileText,
  Phone,
  Loader2,
  UserCheck,
} from 'lucide-react';
import { TEST_ACCOUNTS, UserSession } from '../firebase';
import { useAuth } from '../hooks/useAuth';
import { api } from '../lib/api';
import { getCurrentLocationWithPlaceName } from '../lib/geo';

interface LoginProps {
  onSuccess: (user: UserSession) => void;
}

export const Login: React.FC<LoginProps> = ({ onSuccess }) => {
  const { login } = useAuth();

  // Mode: Sign In or Apply as New Partner (Pending Admin Approval)
  const [mode, setMode] = useState<'signin' | 'register'>('signin');

  // Sign In State
  const [email, setEmail] = useState('donor@gmail.com');
  const [password, setPassword] = useState('1234');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Apply as Partner State
  const [regName, setRegName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('1234');
  const [showRegPassword, setShowRegPassword] = useState(false);
  const [regType, setRegType] = useState<'donor' | 'ngo'>('donor');
  const [regLicense, setRegLicense] = useState('');
  const [regAddress, setRegAddress] = useState('');
  const [regPhone, setRegPhone] = useState('+91 98765 44332');
  const [regLoading, setRegLoading] = useState(false);
  const [regSuccess, setRegSuccess] = useState<string | null>(null);
  const [locating, setLocating] = useState(false);

  // Full list of accounts across all roles with bracket names
  const testAccountsList = [
    // ── NGOs ──
    {
      role: 'ngo',
      title: 'Robin Hood Army Bangalore [Robin Hood Army - NGO]',
      email: 'ngo@gmail.com',
      password: '1234',
      badge: 'Indiranagar Shelter',
      badgeColor: '#0071e3',
      desc: 'Rank #2 NGO in Indiranagar. Receives cascaded surplus offers.',
      icon: <HeartHandshake size={20} color="#0071e3" />,
      account: TEST_ACCOUNTS['ngo@gmail.com'],
    },
    {
      role: 'ngo',
      title: 'Koramangala Community Kitchen [Koramangala Kitchen - NGO]',
      email: 'kitchen@koramangala.org',
      password: '1234',
      badge: 'Koramangala Hub',
      badgeColor: '#0071e3',
      desc: 'Rank #1 NGO for 80 Feet Road Koramangala listings (0.0km away).',
      icon: <HeartHandshake size={20} color="#0071e3" />,
      account: TEST_ACCOUNTS['kitchen@koramangala.org'],
    },
    {
      role: 'ngo',
      title: 'Hasiru Dala Feeding Centre [Hasiru Dala - NGO]',
      email: 'hasiru@feeding.org',
      password: '1234',
      badge: 'KR Market Relief',
      badgeColor: '#0071e3',
      desc: 'Central market community kitchen serving wastepicker families.',
      icon: <HeartHandshake size={20} color="#0071e3" />,
      account: TEST_ACCOUNTS['hasiru@feeding.org'],
    },

    // ── Donors ──
    {
      role: 'donor',
      title: 'Taj Palace Luxury Catering [Taj Palace - Donor]',
      email: 'donor@gmail.com',
      password: '1234',
      badge: 'Hot-Hold Banquets',
      badgeColor: '#1b7a43',
      desc: 'Post corporate lunch/dinner batches with Gemini AI vision & safe_until.',
      icon: <Utensils size={20} color="#1b7a43" />,
      account: TEST_ACCOUNTS['donor@gmail.com'],
    },
    {
      role: 'donor',
      title: 'Grand Convention & Banquets [Grand Banquets - Donor]',
      email: 'grand@banquets.com',
      password: '1234',
      badge: 'Chilled Buffets',
      badgeColor: '#1b7a43',
      desc: 'Koramangala convention hall surplus with chilled holding facilities.',
      icon: <Utensils size={20} color="#1b7a43" />,
      account: TEST_ACCOUNTS['grand@banquets.com'],
    },
    {
      role: 'donor',
      title: 'ITC Gardenia Banquets [ITC Gardenia - Donor]',
      email: 'itc@gardenia.com',
      password: '1234',
      badge: 'Residency Road Hotel',
      badgeColor: '#1b7a43',
      desc: '5-star luxury hospitality donor with verified FSSAI compliance.',
      icon: <Utensils size={20} color="#1b7a43" />,
      account: TEST_ACCOUNTS['itc@gardenia.com'],
    },

    // ── Volunteers ──
    {
      role: 'volunteer',
      title: 'Arun Kumar Courier [Arun Kumar - Volunteer]',
      email: 'volunteer@gmail.com',
      password: '1234',
      badge: 'East Bangalore Driver',
      badgeColor: '#b25e00',
      desc: '2-Opt TSP route planner, temperature logs (>63°C), and proof of delivery.',
      icon: <Truck size={20} color="#b25e00" />,
      account: TEST_ACCOUNTS['volunteer@gmail.com'],
    },
    {
      role: 'volunteer',
      title: 'Priya Sharma Express [Priya Sharma - Volunteer]',
      email: 'priya@courier.org',
      password: '1234',
      badge: 'South Bangalore Driver',
      badgeColor: '#b25e00',
      desc: 'Refrigerated van courier handling chilled bakery & dairy rescues.',
      icon: <Truck size={20} color="#b25e00" />,
      account: TEST_ACCOUNTS['priya@courier.org'],
    },

    // ── Administrator ──
    {
      role: 'admin',
      title: 'FoodBridge Central Admin [System Administrator - Admin]',
      email: 'admin@gmail.com',
      password: '1234',
      badge: 'Platform Ops',
      badgeColor: '#5856d6',
      desc: 'System telemetry, partner verification approvals, and match escalations.',
      icon: <Shield size={20} color="#5856d6" />,
      account: TEST_ACCOUNTS['admin@gmail.com'],
    },
  ];

  const syncPartnerVerification = async (userEmail: string) => {
    const norm = userEmail.trim().toLowerCase();
    try {
      const res = await api.checkPartnerStatus(norm);
      if (res && res.found) {
        // Cache in foodbridge_admin_verifications
        const cachedVers = JSON.parse(localStorage.getItem('foodbridge_admin_verifications') || '[]');
        const existingIdx = cachedVers.findIndex((v: any) => v.email && v.email.toLowerCase() === norm);
        const entry = {
          id: res.id || `req_${Date.now()}`,
          name: res.name,
          email: res.email,
          type: res.type,
          fssai_license: res.fssai_license,
          address: res.address,
          phone: res.phone,
          password: res.password || '1234',
          status: res.status,
          submitted_at: res.submitted_at,
          verified_at: res.verified_at,
        };
        if (existingIdx >= 0) {
          cachedVers[existingIdx] = entry;
        } else {
          cachedVers.unshift(entry);
        }
        localStorage.setItem('foodbridge_admin_verifications', JSON.stringify(cachedVers));

        // Cache in foodbridge_registered_partners
        const partners = JSON.parse(localStorage.getItem('foodbridge_registered_partners') || '{}');
        partners[norm] = {
          ...entry,
          uid: `${res.type}_${Date.now()}`,
        };
        localStorage.setItem('foodbridge_registered_partners', JSON.stringify(partners));
        return;
      }

      // Fallback: query all verifications from GET /admin/verifications
      const vers = await api.getVerifications();
      const found = vers.find((v: any) => v.email && v.email.toLowerCase() === norm);
      if (found) {
        const cachedVers = JSON.parse(localStorage.getItem('foodbridge_admin_verifications') || '[]');
        const existingIdx = cachedVers.findIndex((v: any) => v.email && v.email.toLowerCase() === norm);
        if (existingIdx >= 0) {
          cachedVers[existingIdx] = found;
        } else {
          cachedVers.unshift(found);
        }
        localStorage.setItem('foodbridge_admin_verifications', JSON.stringify(cachedVers));

        const partners = JSON.parse(localStorage.getItem('foodbridge_registered_partners') || '{}');
        partners[norm] = {
          ...(partners[norm] || {}),
          name: found.name,
          email: found.email,
          type: found.type,
          status: found.status,
          fssai_license: found.fssai_license,
          address: found.address,
          phone: found.phone || '+91 98765 00000',
          password: found.password || partners[norm]?.password || '1234',
          uid: `${found.type}_${Date.now()}`,
        };
        localStorage.setItem('foodbridge_registered_partners', JSON.stringify(partners));
      }
    } catch {
      // Offline fallback
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);

    try {
      // Sync verification approval from backend before authenticating
      await syncPartnerVerification(email);
      const session = login(email, password);
      onSuccess(session);
    } catch (err: any) {
      setErrorMsg(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAccount = (accEmail: string, accPass: string) => {
    setEmail(accEmail);
    setPassword(accPass);
    setErrorMsg(null);
    try {
      const session = login(accEmail, accPass);
      onSuccess(session);
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  const handleDetectGPS = async () => {
    setLocating(true);
    try {
      const loc = await getCurrentLocationWithPlaceName();
      setRegAddress(loc.formattedAddress || loc.placeName);
    } catch (e: any) {
      setRegAddress('Koramangala 4th Block, 80 Feet Road, Bengaluru, Karnataka 560034');
    } finally {
      setLocating(false);
    }
  };

  const handleRegisterPartner = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setRegSuccess(null);
    setRegLoading(true);

    try {
      const normEmail = regEmail.trim().toLowerCase();
      const payload = {
        name: regName,
        email: normEmail,
        type: regType,
        fssai_license: regLicense,
        address: regAddress || 'Bangalore Central, Karnataka',
        phone: regPhone,
        password: regPassword || '1234',
      };

      // 1. Submit application to backend /admin/verifications
      await api.applyVerification(payload);

      // 2. Save into registered dynamic partners
      const current = JSON.parse(localStorage.getItem('foodbridge_registered_partners') || '{}');
      current[normEmail] = {
        ...payload,
        uid: `${regType}_${Date.now()}`,
        status: 'pending',
      };
      localStorage.setItem('foodbridge_registered_partners', JSON.stringify(current));

      setRegSuccess(
        `Application submitted for "${regName}"! Status: PENDING Admin Verification. ` +
        `The Platform Administrator must review and approve your application before full access is granted. ` +
        `Sign in as Admin (admin@gmail.com) -> Admin Console -> click 'Approve' to activate this partner.`
      );

      // Pre-fill sign in form with the new email and password
      setEmail(normEmail);
      setPassword(regPassword || '1234');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to submit partner application.');
    } finally {
      setRegLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '960px', margin: '20px auto', padding: '0 16px' }}>
      {/* Brand Header */}
      <div style={{ textAlign: 'center', marginBottom: '28px' }}>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(27, 122, 67, 0.1)',
            color: 'var(--accent-primary)',
            padding: '4px 12px',
            borderRadius: '100px',
            fontSize: '12px',
            fontWeight: 600,
            marginBottom: '10px',
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
          }}
        >
          <Sparkles size={13} />
          <span>Multi-Role Access & Verification Control</span>
        </div>
        <h1
          style={{
            fontSize: '2rem',
            fontWeight: 700,
            color: 'var(--text-primary)',
            letterSpacing: '-0.03em',
            marginBottom: '6px',
          }}
        >
          Sign In to FoodBridge
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13.5px', maxWidth: '580px', margin: '0 auto' }}>
          Select any verified partner account below to experience their perspective, or submit a new partner application for administrator review.
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(320px, 400px) 1fr',
          gap: '24px',
          alignItems: 'start',
        }}
      >
        {/* Left Side: Sign In OR Apply as Partner Form Card */}
        <div className="apple-card" style={{ padding: '24px 26px' }}>
          {/* Mode Switch Tabs */}
          <div
            style={{
              display: 'flex',
              background: 'rgba(0, 0, 0, 0.04)',
              padding: '3px',
              borderRadius: '8px',
              marginBottom: '20px',
            }}
          >
            <button
              type="button"
              onClick={() => {
                setMode('signin');
                setErrorMsg(null);
                setRegSuccess(null);
              }}
              style={{
                flex: 1,
                padding: '7px 0',
                fontSize: '12.5px',
                fontWeight: 600,
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                background: mode === 'signin' ? 'var(--bg-card)' : 'transparent',
                color: mode === 'signin' ? 'var(--text-primary)' : 'var(--text-secondary)',
                boxShadow: mode === 'signin' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                transition: 'all 0.15s ease',
              }}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('register');
                setErrorMsg(null);
                setRegSuccess(null);
              }}
              style={{
                flex: 1,
                padding: '7px 0',
                fontSize: '12.5px',
                fontWeight: 600,
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                background: mode === 'register' ? 'var(--bg-card)' : 'transparent',
                color: mode === 'register' ? 'var(--text-primary)' : 'var(--text-secondary)',
                boxShadow: mode === 'register' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                transition: 'all 0.15s ease',
              }}
            >
              Apply as Partner
            </button>
          </div>

          {/* Success Banner */}
          {regSuccess && (
            <div
              style={{
                background: 'rgba(27, 122, 67, 0.09)',
                border: '1px solid rgba(27, 122, 67, 0.25)',
                borderRadius: 'var(--radius-sm)',
                padding: '12px',
                color: 'var(--accent-primary)',
                marginBottom: '18px',
                fontSize: '12.5px',
                lineHeight: 1.45,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600, marginBottom: '4px' }}>
                <CheckCircle2 size={15} />
                <span>Application Submitted!</span>
              </div>
              <div>{regSuccess}</div>
            </div>
          )}

          {/* Error Banner */}
          {errorMsg && (
            <div
              style={{
                background: 'rgba(215, 0, 21, 0.08)',
                border: '1px solid rgba(215, 0, 21, 0.2)',
                borderRadius: 'var(--radius-sm)',
                padding: '10px 12px',
                color: 'var(--accent-red)',
                marginBottom: '18px',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
                fontSize: '12.5px',
                lineHeight: 1.4,
              }}
            >
              <AlertCircle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>{errorMsg}</div>
            </div>
          )}

          {mode === 'signin' ? (
            /* ── Sign In Form ── */
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '4px', color: 'var(--text-primary)' }}>
                Account Credentials
              </h2>
              <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginBottom: '18px' }}>
                Testing password for all demo accounts: <code style={{ background: 'rgba(0,0,0,0.06)', padding: '2px 5px', borderRadius: '4px', color: 'var(--accent-primary)', fontWeight: 600 }}>1234</code>
              </p>

              <form onSubmit={handleSubmit}>
                {/* Email Field */}
                <div style={{ marginBottom: '14px' }}>
                  <label
                    style={{
                      display: 'block',
                      fontSize: '11.5px',
                      fontWeight: 600,
                      color: 'var(--text-secondary)',
                      marginBottom: '5px',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                    }}
                  >
                    Email Address
                  </label>
                  <div style={{ position: 'relative' }}>
                    <Mail
                      size={15}
                      color="var(--text-tertiary)"
                      style={{ position: 'absolute', left: '12px', top: '12px' }}
                    />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="e.g. donor@gmail.com"
                      style={{
                        width: '100%',
                        padding: '9px 12px 9px 36px',
                        borderRadius: '8px',
                        border: '1px solid var(--border-subtle)',
                        background: 'var(--bg-card)',
                        color: 'var(--text-primary)',
                        fontSize: '13px',
                        outline: 'none',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>
                </div>

                {/* Password Field */}
                <div style={{ marginBottom: '20px' }}>
                  <label
                    style={{
                      display: 'block',
                      fontSize: '11.5px',
                      fontWeight: 600,
                      color: 'var(--text-secondary)',
                      marginBottom: '5px',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                    }}
                  >
                    Password
                  </label>
                  <div style={{ position: 'relative' }}>
                    <Lock
                      size={15}
                      color="var(--text-tertiary)"
                      style={{ position: 'absolute', left: '12px', top: '12px' }}
                    />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••"
                      style={{
                        width: '100%',
                        padding: '9px 38px 9px 36px',
                        borderRadius: '8px',
                        border: '1px solid var(--border-subtle)',
                        background: 'var(--bg-card)',
                        color: 'var(--text-primary)',
                        fontSize: '13px',
                        outline: 'none',
                        boxSizing: 'border-box',
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      style={{
                        position: 'absolute',
                        right: '10px',
                        top: '10px',
                        background: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        color: 'var(--text-tertiary)',
                        padding: 0,
                      }}
                    >
                      {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="btn btn-primary"
                  style={{
                    width: '100%',
                    justifyContent: 'center',
                    padding: '10px',
                    fontSize: '13.5px',
                    fontWeight: 600,
                  }}
                >
                  <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
                  <ArrowRight size={15} />
                </button>
              </form>
            </div>
          ) : (
            /* ── Apply as New Partner Form ── */
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '4px', color: 'var(--text-primary)' }}>
                Apply as Partner
              </h2>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                Commercial donors & verified NGOs must be reviewed by the Administrator before activation.
              </p>

              <form onSubmit={handleRegisterPartner}>
                {/* Partner Role */}
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Partner Type
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <button
                      type="button"
                      onClick={() => setRegType('donor')}
                      style={{
                        padding: '8px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: 600,
                        border: regType === 'donor' ? '1.5px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
                        background: regType === 'donor' ? 'rgba(27,122,67,0.08)' : 'transparent',
                        color: regType === 'donor' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                        cursor: 'pointer',
                      }}
                    >
                      🍲 Food Donor
                    </button>
                    <button
                      type="button"
                      onClick={() => setRegType('ngo')}
                      style={{
                        padding: '8px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: 600,
                        border: regType === 'ngo' ? '1.5px solid var(--accent-blue)' : '1px solid var(--border-subtle)',
                        background: regType === 'ngo' ? 'rgba(0,113,227,0.08)' : 'transparent',
                        color: regType === 'ngo' ? 'var(--accent-blue)' : 'var(--text-secondary)',
                        cursor: 'pointer',
                      }}
                    >
                      🤝 NGO Shelter
                    </button>
                  </div>
                </div>

                {/* Organization Name */}
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Entity / Business Name
                  </label>
                  <input
                    type="text"
                    required
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    placeholder={regType === 'donor' ? 'e.g. Sri Krishna Sweets & Catering' : 'e.g. Sneha Seva Feeding Trust'}
                    className="input-field"
                    style={{ fontSize: '12.5px', padding: '8px 10px' }}
                  />
                </div>

                {/* Email Address */}
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    placeholder="e.g. contact@srikrishnacatering.com"
                    className="input-field"
                    style={{ fontSize: '12.5px', padding: '8px 10px' }}
                  />
                </div>

                {/* Account Password */}
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Account Password
                  </label>
                  <div style={{ position: 'relative' }}>
                    <input
                      type={showRegPassword ? 'text' : 'password'}
                      required
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      placeholder="Choose a password (e.g. 1234)"
                      className="input-field"
                      style={{ fontSize: '12.5px', padding: '8px 36px 8px 10px' }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowRegPassword(!showRegPassword)}
                      style={{
                        position: 'absolute',
                        right: '10px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-tertiary)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                      }}
                      title={showRegPassword ? 'Hide password' : 'Show password'}
                    >
                      {showRegPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>

                {/* FSSAI or NGO License */}
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '4px' }}>
                    {regType === 'donor' ? 'FSSAI Food License No.' : 'NGO Trust Registration No.'}
                  </label>
                  <input
                    type="text"
                    required
                    value={regLicense}
                    onChange={(e) => setRegLicense(e.target.value)}
                    placeholder={regType === 'donor' ? 'e.g. 11228899003344 (14 digits)' : 'e.g. NGO-KA-8891-2024'}
                    className="input-field"
                    style={{ fontSize: '12.5px', padding: '8px 10px' }}
                  />
                </div>

                {/* Kitchen / Facility Address */}
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <label style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                      Operating Address
                    </label>
                    <button
                      type="button"
                      onClick={handleDetectGPS}
                      disabled={locating}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--accent-primary)',
                        fontSize: '11px',
                        cursor: 'pointer',
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '3px',
                      }}
                    >
                      <MapPin size={11} />
                      <span>{locating ? 'Detecting...' : 'Detect GPS'}</span>
                    </button>
                  </div>
                  <input
                    type="text"
                    required
                    value={regAddress}
                    onChange={(e) => setRegAddress(e.target.value)}
                    placeholder="e.g. Koramangala 5th Block, Bengaluru"
                    className="input-field"
                    style={{ fontSize: '12.5px', padding: '8px 10px' }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={regLoading}
                  className="btn btn-primary"
                  style={{
                    width: '100%',
                    justifyContent: 'center',
                    padding: '9px',
                    fontSize: '13px',
                    fontWeight: 600,
                  }}
                >
                  <UserCheck size={14} />
                  <span>{regLoading ? 'Submitting Application...' : 'Submit for Admin Review'}</span>
                </button>
              </form>
            </div>
          )}

          <div
            style={{
              marginTop: '16px',
              paddingTop: '14px',
              borderTop: '1px solid var(--border-subtle)',
              fontSize: '11.5px',
              color: 'var(--text-tertiary)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <CheckCircle2 size={13} color="var(--accent-primary)" />
            <span>FSSAI compliance enforced across all registered partners</span>
          </div>
        </div>

        {/* Right Side: Complete List of All Accounts Across All Roles with Bracket Names */}
        <div>
          <div style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              1-Click Verified Accounts (Password: 1234)
            </span>
            <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
              Click any to sign in directly
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {testAccountsList.map((acc) => {
              const isSelected = email === acc.email;
              return (
                <div
                  key={acc.email}
                  className="apple-card apple-card-interactive"
                  onClick={() => handleSelectAccount(acc.email, acc.password)}
                  style={{
                    padding: '12px 14px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    border: isSelected ? `1.5px solid ${acc.badgeColor}` : '1px solid var(--border-subtle)',
                    background: isSelected ? 'rgba(0, 0, 0, 0.02)' : 'var(--bg-card)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div
                      style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '8px',
                        background: 'rgba(0, 0, 0, 0.04)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}
                    >
                      {acc.icon}
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px', flexWrap: 'wrap' }}>
                        <span style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>
                          {acc.title}
                        </span>
                        <span
                          style={{
                            fontSize: '10px',
                            fontWeight: 600,
                            padding: '1px 6px',
                            borderRadius: '4px',
                            background: `${acc.badgeColor}15`,
                            color: acc.badgeColor,
                          }}
                        >
                          {acc.badge}
                        </span>
                      </div>
                      <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>
                        <code style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {acc.email}
                        </code>
                        {' · '}
                        <span>pass: {acc.password}</span>
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '2px' }}>
                        {acc.desc}
                      </div>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ fontSize: '11px', padding: '5px 10px', flexShrink: 0, marginLeft: '8px' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelectAccount(acc.email, acc.password);
                    }}
                  >
                    Login
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
