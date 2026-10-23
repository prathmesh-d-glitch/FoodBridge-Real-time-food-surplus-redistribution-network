import React, { useState } from 'react';
import { Check, X, Clock } from 'lucide-react';
import { MatchOffer } from '../lib/api';
import { MatchExplainer } from './MatchExplainer';
import { useCountdown } from '../hooks/useCountdown';
import confetti from 'canvas-confetti';

interface OfferCardProps {
  offer: MatchOffer;
  onAccept: (offerId: string) => Promise<void>;
  onDecline: (offerId: string, reason: string) => Promise<void>;
}

export const OfferCard: React.FC<OfferCardProps> = ({ offer, onAccept, onDecline }) => {
  const [loading, setLoading] = useState(false);
  const [declined, setDeclined] = useState(false);
  const { formatted, isExpired } = useCountdown(offer.expires_at);

  const handleAccept = async () => {
    setLoading(true);
    try {
      await onAccept(offer.id);
      confetti({
        particleCount: 50,
        spread: 50,
        origin: { y: 0.6 },
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDecline = async () => {
    setLoading(true);
    try {
      await onDecline(offer.id, 'Capacity full or logistics unavailable');
      setDeclined(true);
    } finally {
      setLoading(false);
    }
  };

  if (declined) {
    return (
      <div className="apple-card" style={{ padding: '18px 20px', opacity: 0.65 }}>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
          Offer declined. Escalating to next ranked recipient...
        </p>
      </div>
    );
  }

  const isOpen = offer.status === 'offered' && !isExpired;

  return (
    <div className="apple-card" style={{ padding: '20px 22px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Cascading Allocation
          </span>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Target: <strong style={{ color: 'var(--text-primary)' }}>{offer.ngo_name}</strong>
          </div>
        </div>

        {isOpen ? (
          <span className="badge badge-amber tabular-numbers">
            <Clock size={12} />
            <span>Cascade Timeout: {formatted}</span>
          </span>
        ) : (
          <span className="badge badge-neutral">Status: {offer.status}</span>
        )}
      </div>

      <div style={{ marginBottom: '12px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '3px' }}>
          Surplus Food Redistribution
        </h3>
        <p style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
          Listing ID: <span style={{ fontFamily: 'var(--font-mono)' }}>{offer.listing_id}</span>
        </p>
      </div>

      {/* 6-Factor Algorithm Explainer */}
      <MatchExplainer
        score={offer.score}
        breakdown={offer.score_breakdown}
        rank={offer.rank}
      />

      {isOpen && (
        <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
          <button
            type="button"
            className="btn btn-primary"
            style={{ flex: 2 }}
            onClick={handleAccept}
            disabled={loading}
          >
            <Check size={14} />
            <span>{loading ? 'Confirming...' : 'Accept Donation'}</span>
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ flex: 1 }}
            onClick={handleDecline}
            disabled={loading}
          >
            <X size={13} />
            <span>Decline</span>
          </button>
        </div>
      )}
    </div>
  );
};
