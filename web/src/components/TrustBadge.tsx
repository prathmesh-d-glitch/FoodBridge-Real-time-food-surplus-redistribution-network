import React from 'react';
import { ShieldCheck, Star, Thermometer } from 'lucide-react';

interface TrustBadgeProps {
  verified?: boolean;
  reliabilityScore?: number;
  temperature?: number;
}

export const TrustBadge: React.FC<TrustBadgeProps> = ({
  verified = true,
  reliabilityScore = 0.95,
  temperature,
}) => {
  return (
    <div
      className="tabular-numbers"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '8px',
        fontSize: '12px',
        color: 'var(--text-secondary)',
      }}
    >
      {verified && (
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '3.5px',
            color: 'var(--accent-primary)',
            fontWeight: 500,
          }}
          title="FSSAI & Regulatory Verification Completed"
        >
          <ShieldCheck size={13} />
          <span>Verified</span>
        </span>
      )}

      {reliabilityScore !== undefined && (
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '3px',
            color: 'var(--text-secondary)',
          }}
          title="Reliability score based on verified handovers"
        >
          <Star size={11} color="var(--accent-orange)" fill="var(--accent-orange)" style={{ opacity: 0.8 }} />
          <span>{(reliabilityScore * 100).toFixed(0)}% Trust</span>
        </span>
      )}

      {temperature !== undefined && (
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '3px',
            color: 'var(--text-secondary)',
          }}
        >
          <Thermometer size={12} color="var(--accent-blue)" />
          <span>{temperature.toFixed(1)}°C</span>
        </span>
      )}
    </div>
  );
};
