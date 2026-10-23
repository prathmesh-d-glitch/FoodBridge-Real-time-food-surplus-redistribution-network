import React from 'react';
import {
  UtensilsCrossed,
  Map,
  Truck,
  HeartHandshake,
  BarChart3,
  ShieldAlert,
  Globe,
  User,
  Plus,
} from 'lucide-react';
import { Language, getTranslation } from '../i18n';
import { UserSession } from '../firebase';

interface LayoutProps {
  children: React.ReactNode;
  activePage: string;
  setActivePage: (page: string) => void;
  language: Language;
  setLanguage: (lang: Language) => void;
  user: UserSession;
  onSwitchRole: (role: 'donor' | 'ngo' | 'volunteer' | 'admin') => void;
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  activePage,
  setActivePage,
  language,
  setLanguage,
  user,
  onSwitchRole,
}) => {
  const t = getTranslation(language);

  const navItems = [
    { id: 'donor', label: t.nav.donor, icon: <UtensilsCrossed size={13} /> },
    { id: 'ngo', label: t.nav.ngo, icon: <HeartHandshake size={13} /> },
    { id: 'volunteer', label: t.nav.volunteer, icon: <Truck size={13} /> },
    { id: 'map', label: t.nav.map, icon: <Map size={13} /> },
    { id: 'impact', label: t.nav.impact, icon: <BarChart3 size={13} /> },
    { id: 'admin', label: t.nav.admin, icon: <ShieldAlert size={13} /> },
  ];

  const currentTab = activePage === 'post_surplus' ? 'donor' : activePage;

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="top-navbar">
        {/* Brand Lockup */}
        <div
          style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', userSelect: 'none' }}
          onClick={() => setActivePage('donor')}
        >
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '6px',
              background: 'var(--accent-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <UtensilsCrossed size={13} color="#ffffff" />
          </div>
          <span style={{ fontSize: '0.95rem', fontWeight: 600, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            FoodBridge
          </span>
        </div>

        {/* Apple Segmented Navigation Bar */}
        <nav className="segmented-nav">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`segmented-nav-btn ${currentTab === item.id ? 'active' : ''}`}
              onClick={() => setActivePage(item.id)}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Utility Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {/* Language Selector */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              background: 'rgba(0, 0, 0, 0.04)',
              padding: '3px 8px',
              borderRadius: '6px',
            }}
          >
            <Globe size={12} color="var(--text-secondary)" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as Language)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-primary)',
                fontSize: '12px',
                fontWeight: 500,
                outline: 'none',
                cursor: 'pointer',
                fontFamily: 'inherit',
              }}
            >
              <option value="en">EN</option>
              <option value="hi">HI</option>
              <option value="kn">KN</option>
            </select>
          </div>

          {/* Role Switcher */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              background: 'rgba(0, 0, 0, 0.04)',
              padding: '3px 9px',
              borderRadius: '6px',
            }}
          >
            <User size={12} color="var(--accent-primary)" />
            <select
              value={user.role}
              onChange={(e) => {
                const newRole = e.target.value as any;
                onSwitchRole(newRole);
                if (newRole === 'donor') setActivePage('donor');
                if (newRole === 'ngo') setActivePage('ngo');
                if (newRole === 'volunteer') setActivePage('volunteer');
                if (newRole === 'admin') setActivePage('admin');
              }}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-primary)',
                fontSize: '12px',
                fontWeight: 500,
                outline: 'none',
                cursor: 'pointer',
                fontFamily: 'inherit',
                textTransform: 'capitalize',
              }}
            >
              <option value="donor">Donor</option>
              <option value="ngo">NGO</option>
              <option value="volunteer">Volunteer</option>
              <option value="admin">Admin</option>
            </select>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {children}
      </main>
    </div>
  );
};
