import React, { useState } from 'react';
import {
  Server,
  UserCheck,
  AlertTriangle,
  Check,
  X,
  Activity,
} from 'lucide-react';
import { UserSession } from '../firebase';

interface AdminConsoleProps {
  user: UserSession;
}

export const AdminConsole: React.FC<AdminConsoleProps> = ({ user }) => {
  const [servicesHealth] = useState<Record<string, boolean>>({
    'listing-service': true,
    'matching-service': true,
    'notification-service': true,
    'logistics-service': true,
    'analytics-service': true,
    'expiry-job': true,
  });

  const [verificationQueue, setVerificationQueue] = useState([
    {
      id: 'req_01',
      name: 'ITC Gardenia Banquets',
      type: 'donor',
      fssai_license: '11223344556677',
      address: 'Residency Road, Bangalore',
      status: 'pending',
    },
    {
      id: 'req_02',
      name: 'Hasiru Dala Feeding Centre',
      type: 'ngo',
      fssai_license: 'NGO-8829-KA',
      address: 'KR Market, Bangalore',
      status: 'pending',
    },
  ]);

  const escalations = [
    {
      id: 'esc_101',
      listing_id: 'list_wedding_rush_3',
      donor: 'Royal Orchid Hotel',
      reason: 'No responses within 15km. Search radius broadened to 30km.',
      timestamp: '12m ago',
      resolved: false,
    },
    {
      id: 'esc_100',
      listing_id: 'list_lunch_rush_1',
      donor: 'Taj Caterers',
      reason: 'Rank 1 NGO response timeout. Escalated to Koramangala Kitchen.',
      timestamp: '34m ago',
      resolved: true,
    },
  ];

  const handleApprove = (id: string) => {
    setVerificationQueue((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: 'verified' } : item))
    );
  };

  const handleReject = (id: string) => {
    setVerificationQueue((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: 'rejected' } : item))
    );
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '4px' }}>
            System Administration
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Microservice telemetry, partner verification queue, and matching escalations
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--accent-primary)', fontWeight: 500 }}>
          <Activity size={14} />
          <span>All Services Operational</span>
        </div>
      </div>

      {/* Microservice Health Indicators */}
      <div className="inset-group" style={{ marginBottom: '24px' }}>
        <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Server size={14} color="var(--accent-primary)" />
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
            Microservices Telemetry
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
          {Object.entries(servicesHealth).map(([svc, ok], idx) => (
            <div
              key={svc}
              style={{
                padding: '12px 18px',
                borderRight: (idx + 1) % 3 !== 0 ? '1px solid var(--border-subtle)' : 'none',
                borderBottom: idx < 3 ? '1px solid var(--border-subtle)' : 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)' }}>
                  {svc}
                </div>
                <div className="tabular-numbers" style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '2px' }}>
                  Port 800{svc.length % 6 + 1}
                </div>
              </div>
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: ok ? 'var(--accent-primary)' : 'var(--accent-red)',
                  boxShadow: ok ? '0 0 0 2px rgba(27, 122, 67, 0.15)' : 'none',
                }}
              />
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(340px, 1.2fr) minmax(300px, 1fr)', gap: '20px' }}>
        {/* Verification Queue */}
        <div>
          <div className="inset-section-label">
            Partner Verification Queue ({verificationQueue.length})
          </div>

          <div className="inset-table">
            {verificationQueue.map((item) => (
              <div
                key={item.id}
                className="inset-table-row"
                style={{ flexDirection: 'column', alignItems: 'stretch', gap: '10px' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <h4 style={{ fontSize: '13.5px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {item.name}
                      </h4>
                      <span className="badge badge-neutral" style={{ fontSize: '10.5px', textTransform: 'uppercase' }}>
                        {item.type}
                      </span>
                    </div>
                    <div className="tabular-numbers" style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '3px' }}>
                      License: <span style={{ fontFamily: 'var(--font-mono)' }}>{item.fssai_license}</span> &bull; {item.address}
                    </div>
                  </div>

                  <span className={`badge ${item.status === 'verified' ? 'badge-green' : item.status === 'rejected' ? 'badge-red' : 'badge-amber'}`}>
                    {item.status}
                  </span>
                </div>

                {item.status === 'pending' && (
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ padding: '3px 12px', fontSize: '12px', minHeight: '28px' }}
                      onClick={() => handleReject(item.id)}
                    >
                      <X size={12} />
                      Reject
                    </button>
                    <button
                      type="button"
                      className="btn btn-primary"
                      style={{ padding: '3px 14px', fontSize: '12px', minHeight: '28px' }}
                      onClick={() => handleApprove(item.id)}
                    >
                      <Check size={13} />
                      Approve
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Escalations Monitor */}
        <div>
          <div className="inset-section-label">
            Matching Escalation Alerts ({escalations.length})
          </div>

          <div className="inset-table">
            {escalations.map((esc) => (
              <div
                key={esc.id}
                className="inset-table-row"
                style={{ flexDirection: 'column', alignItems: 'stretch', gap: '6px' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {esc.donor}
                  </span>
                  <span className="tabular-numbers" style={{ fontSize: '11.5px', color: 'var(--text-tertiary)' }}>
                    {esc.timestamp}
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.45, margin: 0 }}>
                  {esc.reason}
                </p>
                <div style={{ display: 'flex', justifyContent: 'flex-start', marginTop: '2px' }}>
                  <span className={`badge ${esc.resolved ? 'badge-neutral' : 'badge-amber'}`} style={{ fontSize: '11px' }}>
                    {esc.resolved ? 'Resolved' : 'Active Escalation'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
