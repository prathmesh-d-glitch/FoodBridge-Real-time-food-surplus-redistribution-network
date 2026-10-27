import React, { useState } from 'react';
import { Layout } from './components/Layout';
import { useAuth } from './hooks/useAuth';
import { Language } from './i18n';
import { LanguageProvider } from './i18n/context';
import { DonorDashboard } from './pages/DonorDashboard';
import { PostSurplus } from './pages/PostSurplus';
import { NgoFeed } from './pages/NgoFeed';
import { VolunteerRoutePage } from './pages/VolunteerRoute';
import { LiveMapPage } from './pages/LiveMap';
import { ImpactDashboard } from './pages/ImpactDashboard';
import { AdminConsole } from './pages/AdminConsole';
import { Login } from './pages/Login';

export const App: React.FC = () => {
  const { user, switchRole, logout } = useAuth();
  const [activePage, setActivePageState] = useState<string>(() => {
    const hash = window.location.hash.replace('#', '');
    return hash || (user ? user.role : 'login');
  });
  const [language, setLanguage] = useState<Language>('en');

  const setActivePage = (page: string) => {
    setActivePageState(page);
    window.location.hash = page;
  };

  React.useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (hash && hash !== activePage) {
        setActivePageState(hash);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [activePage]);

  // Strict Role Route Guard: restricts each user role to their own pages + common pages (map, impact)
  React.useEffect(() => {
    if (!user) {
      if (activePage !== 'login' && activePage !== 'map' && activePage !== 'impact') {
        setActivePage('login');
      }
      return;
    }

    const allowedPagesByRole: Record<string, string[]> = {
      donor: ['donor', 'post_surplus', 'map', 'impact'],
      ngo: ['ngo', 'map', 'impact'],
      volunteer: ['volunteer', 'map', 'impact'],
      admin: ['admin', 'map', 'impact'],
    };

    const allowed = allowedPagesByRole[user.role] || ['map', 'impact'];
    if (!allowed.includes(activePage)) {
      // Automatically redirect to their assigned primary view
      setActivePage(user.role);
    }
  }, [user?.role, activePage]);

  const handleLogout = () => {
    logout();
    setActivePage('login');
  };

  const renderContent = () => {
    // Common public views accessible by any account type and guests
    if (activePage === 'map') {
      return <LiveMapPage />;
    }
    if (activePage === 'impact') {
      return <ImpactDashboard user={user || undefined} />;
    }

    // Explicit login page or guest state
    if (activePage === 'login' || !user) {
      return (
        <Login
          onSuccess={(u) => {
            setActivePage(u.role);
          }}
        />
      );
    }

    // Role-specific views: strictly render only if authenticated user role matches
    switch (activePage) {
      case 'donor':
        if (user.role === 'donor') {
          return <DonorDashboard user={user} onNavigatePost={() => setActivePage('post_surplus')} />;
        }
        break;
      case 'post_surplus':
        if (user.role === 'donor') {
          return (
            <PostSurplus
              user={user}
              onSuccess={() => setActivePage('donor')}
              onCancel={() => setActivePage('donor')}
            />
          );
        }
        break;
      case 'ngo':
        if (user.role === 'ngo') {
          return <NgoFeed user={user} />;
        }
        break;
      case 'volunteer':
        if (user.role === 'volunteer') {
          return <VolunteerRoutePage user={user} />;
        }
        break;
      case 'admin':
        if (user.role === 'admin') {
          return <AdminConsole user={user} />;
        }
        break;
    }

    // Safe fallback: default to user's assigned role page
    if (user.role === 'donor') return <DonorDashboard user={user} onNavigatePost={() => setActivePage('post_surplus')} />;
    if (user.role === 'ngo') return <NgoFeed user={user} />;
    if (user.role === 'volunteer') return <VolunteerRoutePage user={user} />;
    if (user.role === 'admin') return <AdminConsole user={user} />;
    return <LiveMapPage />;
  };

  return (
    <LanguageProvider language={language} setLanguage={setLanguage}>
      <Layout
        activePage={activePage}
        setActivePage={setActivePage}
        language={language}
        setLanguage={setLanguage}
        user={user}
        onSwitchRole={switchRole}
        onLogout={handleLogout}
      >
        {renderContent()}
      </Layout>
    </LanguageProvider>
  );
};
