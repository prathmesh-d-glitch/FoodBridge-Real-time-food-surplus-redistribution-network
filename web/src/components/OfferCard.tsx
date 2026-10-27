import React, { useState } from 'react';
import { Check, X, Clock, Sparkles, Package, Flame, Droplets, Snowflake, Wind, Scale, Users } from 'lucide-react';
import { MatchOffer } from '../lib/api';
import { MatchExplainer } from './MatchExplainer';
import { useCountdown } from '../hooks/useCountdown';
import confetti from 'canvas-confetti';

interface OfferCardProps {
  offer: MatchOffer;
  onAccept: (offerId: string) => Promise<void>;
  onDecline: (offerId: string, reason: string) => Promise<void>;
}

const storageIcon = (condition?: string) => {
  switch (condition) {
    case 'hot_hold': return <Flame size={12} style={{ color: '#e8630a' }} />;
    case 'chilled': return <Droplets size={12} style={{ color: '#2196f3' }} />;
    case 'frozen': return <Snowflake size={12} style={{ color: '#00bcd4' }} />;
    default: return <Wind size={12} style={{ color: '#888' }} />;
  }
};

const storageLabel = (condition?: string) => {
  switch (condition) {
    case 'hot_hold': return 'Hot Hold (≥63°C)';
    case 'chilled': return 'Chilled (0–5°C)';
    case 'frozen': return 'Frozen (<−18°C)';
    case 'ambient': return 'Ambient Temp';
    default: return condition || 'Unknown';
  }
};

export const OfferCard: React.FC<OfferCardProps> = ({ offer, onAccept, onDecline }) => {
  const [loading, setLoading] = useState(false);
  const [declined, setDeclined] = useState(false);
  const { formatted, isExpired } = useCountdown(offer.expires_at);

  const handleAccept = async () => {
    setLoading(true);
    try {
      await onAccept(offer.id);
      confetti({ particleCount: 60, spread: 55, origin: { y: 0.6 } });
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
      <div className="apple-card" style={{ padding: '18px 20px', opacity: 0.6 }}>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
          Offer declined. Escalating to next ranked recipient...
        </p>
      </div>
    );
  }

  const isOpen = offer.status === 'offered' && !isExpired;
  const ai = offer.listing_photo_analysis;
  const scoreLabel = Math.round(offer.score * 100);

  return (
    <div className="apple-card" style={{ padding: '20px 22px' }}>

      {/* ── Header: title + cascade timeout ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '3px', lineHeight: 1.3 }}>
            {offer.listing_title || 'Surplus Food Redistribution'}
          </h3>
          <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>
            From <strong style={{ color: 'var(--text-primary)' }}>{offer.listing_donor_name || offer.ngo_name}</strong>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '5px' }}>
          {/* Composite score badge */}
          <span
            className="badge"
            style={{
              background: `hsl(${Math.round(scoreLabel * 1.2)}, 70%, 90%)`,
              color: `hsl(${Math.round(scoreLabel * 1.2)}, 60%, 30%)`,
              fontWeight: 700,
              fontSize: '12px',
              padding: '3px 9px',
            }}
          >
            {scoreLabel}/100 Match Score
          </span>
          {isOpen ? (
            <span className="badge badge-amber tabular-numbers" style={{ fontSize: '11px' }}>
              <Clock size={11} />
              <span>Expires: {formatted}</span>
            </span>
          ) : (
            <span className="badge badge-neutral" style={{ fontSize: '11px', textTransform: 'capitalize' }}>
              {offer.status}
            </span>
          )}
        </div>
      </div>

      {/* ── Food Details Row ── */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '8px',
          marginBottom: '12px',
          padding: '10px 12px',
          background: 'rgba(0,0,0,0.03)',
          borderRadius: 'var(--radius-sm)',
        }}
      >
        {offer.listing_quantity_kg != null && (
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            <Scale size={12} />
            <strong style={{ color: 'var(--text-primary)' }}>{offer.listing_quantity_kg} kg</strong>
          </span>
        )}
        {offer.listing_portions != null && (
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            <Users size={12} />
            <strong style={{ color: 'var(--text-primary)' }}>{offer.listing_portions} portions</strong>
          </span>
        )}
        {offer.listing_storage_condition && (
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            {storageIcon(offer.listing_storage_condition)}
            <span>{storageLabel(offer.listing_storage_condition)}</span>
          </span>
        )}
        {offer.listing_safe_until && (
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            <Clock size={12} />
            <span>Safe until {new Date(offer.listing_safe_until).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          </span>
        )}
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--text-tertiary)' }}>
          <Package size={12} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>{offer.listing_id}</span>
        </span>
      </div>

      {/* ── Gemini AI Analysis Badge ── */}
      {ai && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
            alignItems: 'center',
            marginBottom: '12px',
            padding: '8px 12px',
            background: ai.source === 'gemini'
              ? 'linear-gradient(135deg, rgba(66,133,244,0.07), rgba(52,168,83,0.07))'
              : 'rgba(0,0,0,0.03)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid rgba(66,133,244,0.15)',
          }}
        >
          <Sparkles size={13} style={{ color: ai.source === 'gemini' ? '#4285f4' : '#888' }} />
          <span
            style={{
              fontSize: '11.5px',
              fontWeight: 600,
              color: ai.source === 'gemini' ? '#1a73e8' : 'var(--text-secondary)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            {ai.source === 'gemini' ? 'Gemini AI' : 'Analysis'} · {Math.round(ai.confidence * 100)}% confidence
          </span>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            {ai.food_type}
          </span>
          <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
            · {ai.shelf_life_hours_hint}h shelf life
          </span>
          {ai.safety_flags.length > 0 && (
            <span style={{ fontSize: '11px', color: '#e8630a', fontWeight: 500 }}>
              ⚠ {ai.safety_flags[0]}
            </span>
          )}
        </div>
      )}

      {/* ── 6-Factor Score Breakdown ── */}
      <MatchExplainer
        score={offer.score}
        breakdown={offer.score_breakdown}
        rank={offer.rank}
      />

      {/* ── Accept / Decline ── */}
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
