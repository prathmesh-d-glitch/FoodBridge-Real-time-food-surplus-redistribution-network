import React, { useState } from 'react';
import { RefreshCw, HeartHandshake, Check } from 'lucide-react';
import { useOffers } from '../hooks/useOffers';
import { OfferCard } from '../components/OfferCard';
import { api } from '../lib/api';
import { UserSession } from '../firebase';

interface NgoFeedProps {
  user: UserSession;
}

export const NgoFeed: React.FC<NgoFeedProps> = ({ user }) => {
  const { offers, loading, refresh } = useOffers(user.uid);
  const [successMsg, setSuccessMsg] = useState('');

  const activeOffers = offers.filter((o) => o.status === 'offered');
  const pastOffers = offers.filter((o) => o.status !== 'offered');

  const handleAccept = async (offerId: string) => {
    await api.acceptOffer(offerId, user.token);
    setSuccessMsg('Offer accepted. Logistics dispatch initiated.');
    refresh();
    setTimeout(() => setSuccessMsg(''), 5000);
  };

  const handleDecline = async (offerId: string, reason: string) => {
    await api.declineOffer(offerId, reason, user.token);
    refresh();
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.025em', marginBottom: '3px' }}>
            Recipient Offer Feed
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            {user.name} &bull; Ranked by Spoilage-Aware Composite Scoring
          </p>
        </div>

        <button type="button" className="btn btn-secondary" onClick={refresh}>
          <RefreshCw size={13} />
          <span>Refresh</span>
        </button>
      </div>

      {successMsg && (
        <div
          style={{
            background: 'rgba(27, 122, 67, 0.08)',
            border: '1px solid rgba(27, 122, 67, 0.2)',
            borderRadius: 'var(--radius-sm)',
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
          <Check size={15} />
          <span>{successMsg}</span>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-tertiary)', fontSize: '13px' }}>
          Checking active offers...
        </div>
      ) : activeOffers.length === 0 ? (
        <div style={{ padding: '64px 24px', textAlign: 'center', maxWidth: '460px', margin: '40px auto' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              background: 'rgba(0, 0, 0, 0.04)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 14px',
              color: 'var(--text-secondary)',
            }}
          >
            <HeartHandshake size={18} />
          </div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
            No Pending Surplus Offers
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.5, margin: 0 }}>
            When nearby caterers post surplus food matching your capacity and dietary restrictions, cascading allocations will appear here in real time.
          </p>
        </div>
      ) : (
        <div style={{ marginBottom: '32px' }}>
          <div className="inset-section-label">
            Pending Offers ({activeOffers.length})
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {activeOffers.map((offer) => (
              <OfferCard
                key={offer.id}
                offer={offer}
                onAccept={handleAccept}
                onDecline={handleDecline}
              />
            ))}
          </div>
        </div>
      )}

      {/* Resolved Offers */}
      {pastOffers.length > 0 && (
        <div style={{ marginTop: '32px' }}>
          <div className="inset-section-label">
            Resolved Offers ({pastOffers.length})
          </div>

          <div className="inset-table">
            {pastOffers.slice(0, 5).map((po) => (
              <div
                key={po.id}
                className="inset-table-row"
              >
                <div>
                  <div style={{ fontWeight: 500, color: 'var(--text-primary)', fontSize: '13px' }}>
                    Listing: <span style={{ fontFamily: 'var(--font-mono)' }}>{po.listing_id}</span>
                  </div>
                  <div className="tabular-numbers" style={{ fontSize: '11.5px', color: 'var(--text-tertiary)', marginTop: '2px' }}>
                    Offered at {new Date(po.offered_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
                <span
                  className={`badge ${
                    po.status === 'accepted'
                      ? 'badge-green'
                      : po.status === 'declined'
                      ? 'badge-red'
                      : 'badge-neutral'
                  }`}
                  style={{ textTransform: 'capitalize' }}
                >
                  {po.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
