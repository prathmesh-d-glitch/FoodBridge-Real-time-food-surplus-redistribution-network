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

  const handleLogout = () => {
    logout();
    setActivePage('login');
  };

  const renderContent = () => {
    // Public routes that don't require login
    if (activePage === 'map') {
      return <LiveMapPage />;
    }
    if (activePage === 'impact') {
      return <ImpactDashboard user={user || undefined} />;
    }

    // Explicit login page or not logged in
    if (activePage === 'login' || !user) {
      return (
        <Login
          onSuccess={(u) => {
            setActivePage(u.role);
          }}
        />
      );
    }

    // Protected role routes
    switch (activePage) {
      case 'donor':
        return <DonorDashboard user={user} onNavigatePost={() => setActivePage('post_surplus')} />;
      case 'post_surplus':
        return (
          <PostSurplus
            user={user}
            onSuccess={() => setActivePage('donor')}
            onCancel={() => setActivePage('donor')}
          />
        );
      case 'ngo':
        return <NgoFeed user={user} />;
      case 'volunteer':
        return <VolunteerRoutePage user={user} />;
      case 'admin':
        return <AdminConsole user={user} />;
      default:
        return <DonorDashboard user={user} onNavigatePost={() => setActivePage('post_surplus')} />;
    }
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
