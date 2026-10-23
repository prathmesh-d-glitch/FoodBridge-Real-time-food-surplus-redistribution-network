import React from 'react';
import { Shield, Utensils, HeartHandshake, Truck } from 'lucide-react';
import { PRESET_USERS, UserSession } from '../firebase';

interface LoginProps {
  onSelectUser: (user: UserSession) => void;
}

export const Login: React.FC<LoginProps> = ({ onSelectUser }) => {
  const roles = [
    {
      role: 'donor',
      title: 'Donor / Caterer',
      desc: 'Post surplus cooked meals, inspect quality with Gemini AI, and track sustainability impact.',
      icon: <Utensils size={18} color="var(--accent-primary)" />,
      user: PRESET_USERS.donor,
    },
    {
      role: 'ngo',
      title: 'NGO / Shelter',
      desc: 'Review incoming food redistribution offers with explainable matching scores and freshness clocks.',
      icon: <HeartHandshake size={18} color="var(--accent-blue)" />,
      user: PRESET_USERS.ngo,
    },
    {
      role: 'volunteer',
      title: 'Volunteer Driver',
      desc: 'Execute 2-Opt TSP optimized delivery routes with deadline constraints and handover logs.',
      icon: <Truck size={18} color="var(--accent-orange)" />,
      user: PRESET_USERS.volunteer,
    },
    {
      role: 'admin',
      title: 'Administrator',
      desc: 'Monitor microservices health, verify organizations, and manage matching escalations.',
      icon: <Shield size={18} color="var(--accent-primary)" />,
      user: PRESET_USERS.admin,
    },
  ];

  return (
    <div style={{ maxWidth: '800px', margin: '32px auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '28px' }}>
        <h2 style={{ fontSize: '1.75rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.025em', marginBottom: '4px' }}>
          Select Portal Persona
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', maxWidth: '500px', margin: '0 auto' }}>
          Choose a role to experience the real-time food surplus redistribution workflow.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '14px' }}>
        {roles.map((r) => (
          <div
            key={r.role}
            className="apple-card apple-card-interactive"
            onClick={() => onSelectUser(r.user)}
            style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
          >
            <div>
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(0, 0, 0, 0.04)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '12px',
                }}
              >
                {r.icon}
              </div>
              <h3 style={{ fontSize: '1.08rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
                {r.title}
              </h3>
              <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.45, marginBottom: '16px' }}>
                {r.desc}
              </p>
            </div>
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-tertiary)' }}>Profile:</div>
              <div style={{ fontSize: '0.84rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                {r.user.name}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
