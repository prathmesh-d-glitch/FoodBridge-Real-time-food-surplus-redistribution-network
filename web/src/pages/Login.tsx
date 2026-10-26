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
} from 'lucide-react';
import { TEST_ACCOUNTS, UserSession } from '../firebase';
import { useAuth } from '../hooks/useAuth';

interface LoginProps {
  onSuccess: (user: UserSession) => void;
}

export const Login: React.FC<LoginProps> = ({ onSuccess }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('admin@gmail.com');
  const [password, setPassword] = useState('1234');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const testAccountsList = [
    {
      role: 'admin',
      title: 'Administrator',
      email: 'admin@gmail.com',
      password: '1234',
      badge: 'Admin Access',
      badgeColor: '#5856d6',
      desc: 'System telemetry, donor approvals, and match escalations.',
      icon: <Shield size={20} color="#5856d6" />,
      account: TEST_ACCOUNTS['admin@gmail.com'],
    },
    {
      role: 'donor',
      title: 'Donor / Caterer',
      email: 'donor@gmail.com',
      password: '1234',
      badge: 'Donor Portal',
      badgeColor: '#1b7a43',
      desc: 'Post surplus batches, AI spoilage analysis, and CSR certs.',
      icon: <Utensils size={20} color="#1b7a43" />,
      account: TEST_ACCOUNTS['donor@gmail.com'],
    },
    {
      role: 'ngo',
      title: 'NGO / Shelter',
      email: 'ngo@gmail.com',
      password: '1234',
      badge: 'NGO Receiver',
      badgeColor: '#0071e3',
      desc: 'Live freshness clocks, capacity matching, and instant claims.',
      icon: <HeartHandshake size={20} color="#0071e3" />,
      account: TEST_ACCOUNTS['ngo@gmail.com'],
    },
    {
      role: 'volunteer',
      title: 'Volunteer Courier',
      email: 'volunteer@gmail.com',
      password: '1234',
      badge: 'Courier Route',
      badgeColor: '#b25e00',
      desc: '2-Opt TSP route planner, temperature logs, and proof of delivery.',
      icon: <Truck size={20} color="#b25e00" />,
      account: TEST_ACCOUNTS['volunteer@gmail.com'],
    },
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);

    try {
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

  return (
    <div style={{ maxWidth: '840px', margin: '24px auto', padding: '0 16px' }}>
      {/* Brand Header */}
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
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
          <span>Cloud-Native Authentication</span>
        </div>
        <h1
          style={{
            fontSize: '2rem',
            fontWeight: 700,
            color: 'var(--text-primary)',
            letterSpacing: '-0.03em',
            marginBottom: '8px',
          }}
        >
          Sign In to FoodBridge
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px', maxWidth: '520px', margin: '0 auto' }}>
          Access the real-time food redistribution mesh. Enter credentials or click any pre-configured test account below.
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(300px, 380px) 1fr',
          gap: '24px',
          alignItems: 'start',
        }}
      >
        {/* Sign In Form Card */}
        <div className="apple-card" style={{ padding: '28px' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '4px', color: 'var(--text-primary)' }}>
            Account Credentials
          </h2>
          <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
            Testing with password <code style={{ background: 'rgba(0,0,0,0.06)', padding: '2px 5px', borderRadius: '4px', color: 'var(--accent-primary)', fontWeight: 600 }}>1234</code>
          </p>

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

          <form onSubmit={handleSubmit}>
            {/* Email Field */}
            <div style={{ marginBottom: '16px' }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '12px',
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  marginBottom: '6px',
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
                  placeholder="admin@gmail.com"
                  style={{
                    width: '100%',
                    padding: '10px 12px 10px 36px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-card)',
                    color: 'var(--text-primary)',
                    fontSize: '13.5px',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
            </div>

            {/* Password Field */}
            <div style={{ marginBottom: '22px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label
                  style={{
                    fontSize: '12px',
                    fontWeight: 600,
                    color: 'var(--text-secondary)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                  }}
                >
                  Password
                </label>
                <span style={{ fontSize: '11px', color: 'var(--accent-primary)', fontWeight: 500 }}>
                  Test pass: 1234
                </span>
              </div>
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
                  placeholder="Enter 1234"
                  style={{
                    width: '100%',
                    padding: '10px 38px 10px 36px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-card)',
                    color: 'var(--text-primary)',
                    fontSize: '13.5px',
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
                    color: 'var(--text-tertiary)',
                    cursor: 'pointer',
                    padding: '2px',
                  }}
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
              style={{
                width: '100%',
                padding: '11px',
                fontSize: '14px',
                fontWeight: 600,
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
              <ArrowRight size={15} />
            </button>
          </form>

          <div
            style={{
              marginTop: '18px',
              paddingTop: '16px',
              borderTop: '1px solid var(--border-subtle)',
              fontSize: '12px',
              color: 'var(--text-tertiary)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <CheckCircle2 size={13} color="var(--accent-primary)" />
            <span>Mock Auth compatible with Firebase Custom Claims</span>
          </div>
        </div>

        {/* 1-Click Quick Testing Accounts */}
        <div>
          <div style={{ marginBottom: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              1-Click Test Accounts (Password: 1234)
            </span>
            <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
              Click any to sign in directly
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {testAccountsList.map((acc) => {
              const isSelected = email === acc.email;
              return (
                <div
                  key={acc.email}
                  className="apple-card apple-card-interactive"
                  onClick={() => handleSelectAccount(acc.email, acc.password)}
                  style={{
                    padding: '16px 18px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    border: isSelected ? `1.5px solid ${acc.badgeColor}` : '1px solid var(--border-subtle)',
                    background: isSelected ? 'rgba(0, 0, 0, 0.02)' : 'var(--bg-card)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div
                      style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '10px',
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
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                        <span style={{ fontWeight: 600, fontSize: '13.5px', color: 'var(--text-primary)' }}>
                          {acc.title}
                        </span>
                        <span
                          style={{
                            fontSize: '10.5px',
                            fontWeight: 600,
                            padding: '2px 7px',
                            borderRadius: '4px',
                            background: `${acc.badgeColor}15`,
                            color: acc.badgeColor,
                          }}
                        >
                          {acc.badge}
                        </span>
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        <code style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {acc.email}
                        </code>
                        {' · '}
                        <span>pass: {acc.password}</span>
                      </div>
                      <div style={{ fontSize: '11.5px', color: 'var(--text-tertiary)', marginTop: '2px' }}>
                        {acc.desc}
                      </div>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ fontSize: '11.5px', padding: '6px 12px', flexShrink: 0 }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelectAccount(acc.email, acc.password);
                    }}
                  >
                    Quick Login
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
