import React, { useState } from 'react';
import { Layout } from './components/Layout';
import { useAuth } from './hooks/useAuth';
import { Language } from './i18n';
import { DonorDashboard } from './pages/DonorDashboard';
import { PostSurplus } from './pages/PostSurplus';
import { NgoFeed } from './pages/NgoFeed';
import { VolunteerRoutePage } from './pages/VolunteerRoute';
import { LiveMapPage } from './pages/LiveMap';
import { ImpactDashboard } from './pages/ImpactDashboard';
import { AdminConsole } from './pages/AdminConsole';
import { Login } from './pages/Login';

export const App: React.FC = () => {
  const { user, switchRole } = useAuth();
  const [activePage, setActivePageState] = useState<string>(() => {
    const hash = window.location.hash.replace('#', '');
    return hash || 'donor';
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

  const renderContent = () => {
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
      case 'map':
        return <LiveMapPage />;
      case 'impact':
        return <ImpactDashboard user={user} />;
      case 'admin':
        return <AdminConsole user={user} />;
      case 'login':
        return (
          <Login
            onSelectUser={(u) => {
              switchRole(u.role);
              setActivePage(u.role);
            }}
          />
        );
      default:
        return <DonorDashboard user={user} onNavigatePost={() => setActivePage('post_surplus')} />;
    }
  };

  return (
    <Layout
      activePage={activePage}
      setActivePage={setActivePage}
      language={language}
      setLanguage={setLanguage}
      user={user}
      onSwitchRole={switchRole}
    >
      {renderContent()}
    </Layout>
  );
};
