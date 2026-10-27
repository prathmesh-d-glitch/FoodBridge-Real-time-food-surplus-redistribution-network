import React, { useState } from 'react';
import {
  UtensilsCrossed,
  Map,
  Truck,
  HeartHandshake,
  BarChart3,
  ShieldAlert,
  Globe,
  User,
  LogOut,
  LogIn,
  MapPin,
  Navigation,
  Loader2,
  Check,
} from 'lucide-react';
import { Language, getTranslation } from '../i18n';
import { useLanguage } from '../i18n/context';
import { TEST_ACCOUNTS, UserSession } from '../firebase';
import { getCurrentLocationWithPlaceName, formatCoordinates } from '../lib/geo';

interface LayoutProps {
  children: React.ReactNode;
  activePage: string;
  setActivePage: (page: string) => void;
  language: Language;
  setLanguage: (lang: Language) => void;
  user: UserSession | null;
  onSwitchRole: (roleOrEmail: string) => void;
  onLogout?: () => void;
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  activePage,
  setActivePage,
  language,
  setLanguage,
  user,
  onSwitchRole,
  onLogout,
}) => {
  const t = getTranslation(language);
  // Also pull from context so Layout re-renders on language change
  const { t: tc } = useLanguage();

  // Global header location indicator
  const [currentPlace, setCurrentPlace] = useState('Palace Grounds, Bengaluru');
  const [coordsSummary, setCoordsSummary] = useState('12.9716° N, 77.5946° E');
  const [locating, setLocating] = useState(false);
  const [locationPillSuccess, setLocationPillSuccess] = useState(false);

  // Role-specific navigation items: each role sees ONLY their own page + common details (Map & Impact)
  const roleNavMap: Record<string, { id: string; label: string; icon: React.ReactNode }> = {
    donor: { id: 'donor', label: t.nav.donor, icon: <UtensilsCrossed size={13} /> },
    ngo: { id: 'ngo', label: t.nav.ngo, icon: <HeartHandshake size={13} /> },
    volunteer: { id: 'volunteer', label: t.nav.volunteer, icon: <Truck size={13} /> },
    admin: { id: 'admin', label: t.nav.admin, icon: <ShieldAlert size={13} /> },
  };

  const commonNavItems = [
    { id: 'map', label: t.nav.map, icon: <Map size={13} /> },
    { id: 'impact', label: t.nav.impact, icon: <BarChart3 size={13} /> },
  ];

  const roleItem = user?.role ? roleNavMap[user.role] : null;
  const navItems = roleItem ? [roleItem, ...commonNavItems] : commonNavItems;

  const currentTab = activePage === 'post_surplus' ? 'donor' : activePage;

  const handleHeaderDetectLocation = async () => {
    setLocating(true);
    setLocationPillSuccess(false);
    try {
      const loc = await getCurrentLocationWithPlaceName();
      setCurrentPlace(loc.placeName);
      setCoordsSummary(formatCoordinates(loc.latitude, loc.longitude));
      setLocationPillSuccess(true);
      setTimeout(() => setLocationPillSuccess(false), 4000);
    } catch (err: any) {
      alert(err.message || 'Could not access GPS. Please check browser location permissions.');
    } finally {
      setLocating(false);
    }
  };

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="top-navbar">
        {/* Brand Lockup */}
        <div
          style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', userSelect: 'none' }}
          onClick={() => setActivePage(user ? user.role : 'map')}
        >
          <div
            style={{
              width: '26px',
              height: '26px',
              borderRadius: '7px',
              background: 'var(--accent-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 5px rgba(27, 122, 67, 0.25)',
            }}
          >
            <UtensilsCrossed size={14} color="#ffffff" />
          </div>
          <span style={{ fontSize: '1rem', fontWeight: 700, letterSpacing: '-0.025em', color: 'var(--text-primary)' }}>
            FoodBridge
          </span>
        </div>

        {/* Segmented Navigation Bar - strictly scoped to current account type + common details */}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Real-time Location Pill & Reverse Geocoded Place Name */}
          <button
            type="button"
            onClick={handleHeaderDetectLocation}
            disabled={locating}
            title={`Detected Place: ${currentPlace} (${coordsSummary}). Click to refresh location.`}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              background: locationPillSuccess ? 'rgba(27, 122, 67, 0.12)' : 'rgba(0, 0, 0, 0.04)',
              border: locationPillSuccess ? '1px solid rgba(27, 122, 67, 0.3)' : '1px solid transparent',
              padding: '4px 10px',
              borderRadius: '100px',
              fontSize: '11.5px',
              fontWeight: 500,
              color: locationPillSuccess ? 'var(--accent-primary)' : 'var(--text-secondary)',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              maxWidth: '220px',
            }}
          >
            {locating ? (
              <Loader2 size={12} className="spin" color="var(--accent-primary)" />
            ) : locationPillSuccess ? (
              <Check size={12} color="var(--accent-primary)" />
            ) : (
              <MapPin size={12} color="var(--accent-primary)" />
            )}
            <span
              style={{
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {locating ? tc.common.detecting_place : currentPlace}
            </span>
          </button>

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

          {/* User Session Profile & Controls */}
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {/* Active Account Pill & Quick Switcher */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'rgba(0, 0, 0, 0.04)',
                  padding: '3px 8px',
                  borderRadius: '6px',
                }}
              >
                <span
                  style={{
                    fontSize: '10.5px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    color:
                      user.role === 'admin'
                        ? '#5856d6'
                        : user.role === 'donor'
                        ? 'var(--accent-primary)'
                        : user.role === 'ngo'
                        ? '#0071e3'
                        : '#b25e00',
                    background:
                      user.role === 'admin'
                        ? 'rgba(88, 86, 214, 0.12)'
                        : user.role === 'donor'
                        ? 'rgba(27, 122, 67, 0.12)'
                        : user.role === 'ngo'
                        ? 'rgba(0, 113, 227, 0.12)'
                        : 'rgba(178, 94, 0, 0.12)',
                  }}
                >
                  {user.role}
                </span>
                <select
                  value={user.email}
                  onChange={(e) => {
                    const newEmail = e.target.value;
                    onSwitchRole(newEmail);
                    const acc = TEST_ACCOUNTS[newEmail];
                    if (acc) {
                      setActivePage(acc.role);
                    }
                  }}
                  title="Switch logged in account"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-primary)',
                    fontSize: '12px',
                    fontWeight: 600,
                    outline: 'none',
                    cursor: 'pointer',
                    fontFamily: 'inherit',
                  }}
                >
                  <optgroup label="── NGOs / Food Banks ──">
                    <option value="ngo@gmail.com">ngo@gmail.com [Robin Hood Army - NGO]</option>
                    <option value="kitchen@koramangala.org">kitchen@koramangala.org [Koramangala Kitchen - NGO]</option>
                    <option value="hasiru@feeding.org">hasiru@feeding.org [Hasiru Dala - NGO]</option>
                  </optgroup>
                  <optgroup label="── Donors / Caterers ──">
                    <option value="donor@gmail.com">donor@gmail.com [Taj Palace - Donor]</option>
                    <option value="grand@banquets.com">grand@banquets.com [Grand Banquets - Donor]</option>
                    <option value="itc@gardenia.com">itc@gardenia.com [ITC Gardenia - Donor]</option>
                  </optgroup>
                  <optgroup label="── Volunteer Couriers ──">
                    <option value="volunteer@gmail.com">volunteer@gmail.com [Arun Kumar - Volunteer]</option>
                    <option value="priya@courier.org">priya@courier.org [Priya Sharma - Volunteer]</option>
                  </optgroup>
                  <optgroup label="── System Administration ──">
                    <option value="admin@gmail.com">admin@gmail.com [System Administrator - Admin]</option>
                  </optgroup>
                </select>
              </div>

              {/* Logout Button */}
              {onLogout && (
                <button
                  type="button"
                  onClick={onLogout}
                  title="Sign out of FoodBridge"
                  style={{
                    background: 'rgba(215, 0, 21, 0.07)',
                    border: 'none',
                    color: 'var(--accent-red)',
                    padding: '5px 8px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '11.5px',
                    fontWeight: 500,
                  }}
                >
                  <LogOut size={12} />
                  <span>{tc.common.exit}</span>
                </button>
              )}
            </div>
          ) : (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setActivePage('login')}
              style={{ padding: '4px 12px', fontSize: '12px', minHeight: '28px' }}
            >
              <LogIn size={13} />
              <span>{tc.common.sign_in}</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">{children}</main>
    </div>
  );
};
