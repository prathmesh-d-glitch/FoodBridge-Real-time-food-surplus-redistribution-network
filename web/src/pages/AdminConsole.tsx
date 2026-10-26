import React, { useEffect, useState } from 'react';
import {
  Server,
  UserCheck,
  AlertTriangle,
  Check,
  X,
  Activity,
  RefreshCw,
  CheckCircle2,
  ShieldCheck,
} from 'lucide-react';
import { api, PartnerVerification, EscalationAlert, ServiceTelemetry } from '../lib/api';
import { UserSession } from '../firebase';
import { useLanguage } from '../i18n/context';

interface AdminConsoleProps {
  user: UserSession;
}

export const AdminConsole: React.FC<AdminConsoleProps> = ({ user }) => {
  const { t } = useLanguage();
  const [telemetry, setTelemetry] = useState<ServiceTelemetry>({
    'listing-service': { healthy: true, port: 8001, latency_ms: 12.4 },
    'matching-service': { healthy: true, port: 8002, latency_ms: 15.1 },
    'notification-service': { healthy: true, port: 8003, latency_ms: 8.9 },
    'logistics-service': { healthy: true, port: 8004, latency_ms: 11.2 },
    'analytics-service': { healthy: true, port: 8005, latency_ms: 14.5 },
    'expiry-job': { healthy: true, port: 8006, latency_ms: 9.0 },
  });

  const [verificationQueue, setVerificationQueue] = useState<PartnerVerification[]>([]);
  const [escalations, setEscalations] = useState<EscalationAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshingTelemetry, setRefreshingTelemetry] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const loadAllAdminData = async () => {
    setLoading(true);
    try {
      const [vers, escs, telem] = await Promise.all([
        api.getVerifications(),
        api.getEscalations(),
        api.getHealthTelemetry(),
      ]);
      setVerificationQueue(vers);
      setEscalations(escs);
      setTelemetry(telem);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshTelemetry = async () => {
    setRefreshingTelemetry(true);
    try {
      const telem = await api.getHealthTelemetry();
      setTelemetry(telem);
    } finally {
      setRefreshingTelemetry(false);
    }
  };

  useEffect(() => {
    loadAllAdminData();
    const interval = setInterval(loadAllAdminData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = async (id: string, name: string) => {
    // Optimistic UI update
    setVerificationQueue((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: 'verified' } : item))
    );
    setActionNotice(`${t.admin.approved_partner} "${name}". ${t.admin.persisted}`);
    setTimeout(() => setActionNotice(null), 4000);

    // Call persistent backend API
    await api.approveVerification(id, user.token);
  };

  const handleReject = async (id: string, name: string) => {
    setVerificationQueue((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: 'rejected' } : item))
    );
    setActionNotice(`${t.admin.rejected_partner} "${name}". ${t.admin.persisted}`);
    setTimeout(() => setActionNotice(null), 4000);

    await api.rejectVerification(id, user.token);
  };

  const handleResolveEscalation = async (escId: string) => {
    setEscalations((prev) =>
      prev.map((esc) => (esc.id === escId ? { ...esc, resolved: true } : esc))
    );
    setActionNotice(`${t.admin.escalation_resolved}`);
    setTimeout(() => setActionNotice(null), 4000);

    await api.resolveEscalation(escId, user.token);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '4px' }}>
            {t.admin.title}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            {t.admin.subtitle}
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={loadAllAdminData}
            style={{ fontSize: '12px', padding: '5px 12px' }}
          >
            <RefreshCw size={12} className={loading ? 'spin' : ''} />
            <span>{t.admin.sync_data}</span>
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12.5px', color: 'var(--accent-primary)', fontWeight: 500 }}>
            <Activity size={14} />
            <span>{t.admin.platform_active}</span>
          </div>
        </div>
      </div>

      {actionNotice && (
        <div
          style={{
            background: 'rgba(27, 122, 67, 0.08)',
            border: '1px solid rgba(27, 122, 67, 0.25)',
            borderRadius: '8px',
            padding: '10px 14px',
            color: 'var(--accent-primary)',
            marginBottom: '18px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            fontWeight: 500,
          }}
        >
          <CheckCircle2 size={15} />
          <span>{actionNotice}</span>
        </div>
      )}

      {/* Microservice Health Indicators */}
      <div className="inset-group" style={{ marginBottom: '24px' }}>
        <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Server size={14} color="var(--accent-primary)" />
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              {t.admin.telemetry_title}
            </span>
          </div>
          <button
            type="button"
            onClick={handleRefreshTelemetry}
            className="btn btn-tertiary"
            style={{ padding: '2px 8px', fontSize: '11.5px', minHeight: '24px' }}
          >
            <RefreshCw size={11} className={refreshingTelemetry ? 'spin' : ''} />
            <span>{t.admin.probe_health}</span>
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
          {Object.entries(telemetry).map(([svc, info], idx) => (
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
                  {t.admin.port} {info.port} {info.latency_ms ? `· ${info.latency_ms}ms` : ''}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    width: '7px',
                    height: '7px',
                    borderRadius: '50%',
                    background: info.healthy ? 'var(--accent-primary)' : 'var(--accent-red)',
                    boxShadow: info.healthy ? '0 0 0 2px rgba(27, 122, 67, 0.2)' : 'none',
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(340px, 1.2fr) minmax(300px, 1fr)', gap: '20px' }}>
        {/* Verification Queue */}
        <div>
          <div className="inset-section-label">
            {t.admin.verification_queue} ({verificationQueue.length})
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
                      {t.admin.license}: <span style={{ fontFamily: 'var(--font-mono)' }}>{item.fssai_license}</span> &bull; {item.address}
                    </div>
                  </div>

                  <span className={`badge ${item.status === 'verified' ? 'badge-green' : item.status === 'rejected' ? 'badge-red' : 'badge-amber'}`}>
                    {item.status}
                  </span>
                </div>

                {item.status === 'pending' ? (
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ padding: '3px 12px', fontSize: '12px', minHeight: '28px' }}
                      onClick={() => handleReject(item.id, item.name)}
                    >
                      <X size={12} />
                      {t.admin.reject}
                    </button>
                    <button
                      type="button"
                      className="btn btn-primary"
                      style={{ padding: '3px 14px', fontSize: '12px', minHeight: '28px' }}
                      onClick={() => handleApprove(item.id, item.name)}
                    >
                      <Check size={13} />
                      {t.admin.approve}
                    </button>
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11.5px', color: item.status === 'verified' ? 'var(--accent-primary)' : 'var(--accent-red)', paddingTop: '4px' }}>
                    {item.status === 'verified' ? <ShieldCheck size={13} /> : <X size={13} />}
                    <span>{t.admin.status_saved}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Escalations Monitor */}
        <div>
          <div className="inset-section-label">
            {t.admin.escalations_title} ({escalations.length})
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
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                  <span className={`badge ${esc.resolved ? 'badge-neutral' : 'badge-amber'}`} style={{ fontSize: '11px' }}>
                    {esc.resolved ? t.admin.resolved : t.admin.active_escalation}
                  </span>

                  {!esc.resolved && (
                    <button
                      type="button"
                      onClick={() => handleResolveEscalation(esc.id)}
                      className="btn btn-secondary"
                      style={{ padding: '2px 8px', fontSize: '11px', minHeight: '24px' }}
                    >
                      {t.admin.mark_resolved}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
