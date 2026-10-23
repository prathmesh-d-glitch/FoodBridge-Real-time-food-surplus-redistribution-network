import React from 'react';
import { getFreshnessState, getRemainingMinutes } from '../lib/time';

interface FreshnessClockProps {
  safeUntil: string;
  size?: 'sm' | 'md' | 'lg';
}

export const FreshnessClock: React.FC<FreshnessClockProps> = ({ safeUntil, size = 'md' }) => {
  const remMinutes = getRemainingMinutes(safeUntil);
  const state = getFreshnessState(remMinutes);

  const hours = Math.floor(remMinutes / 60);
  const mins = remMinutes % 60;
  const timeText = hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;

  const theme = {
    fresh: {
      bg: 'rgba(27, 122, 67, 0.08)',
      text: '#1b7a43',
      dot: '#1b7a43',
      label: 'Fresh',
    },
    warning: {
      bg: 'rgba(178, 94, 0, 0.09)',
      text: '#b25e00',
      dot: '#b25e00',
      label: 'Expiring Soon',
    },
    urgent: {
      bg: 'rgba(215, 0, 21, 0.08)',
      text: '#d70015',
      dot: '#d70015',
      label: 'Urgent',
    },
    expired: {
      bg: 'rgba(0, 0, 0, 0.05)',
      text: '#86868b',
      dot: '#86868b',
      label: 'Expired',
    },
  }[state];

  return (
    <div
      className="tabular-numbers"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: size === 'sm' ? '3px 8px' : '4px 10px',
        borderRadius: '6px',
        background: theme.bg,
        fontSize: size === 'sm' ? '12px' : '13px',
        color: theme.text,
        fontWeight: 500,
        userSelect: 'none',
      }}
      title={`Safe until: ${new Date(safeUntil).toLocaleTimeString()}`}
    >
      <span
        style={{
          width: '5px',
          height: '5px',
          borderRadius: '50%',
          backgroundColor: theme.dot,
          flexShrink: 0,
        }}
      />
      {state === 'expired' ? (
        <span>Expired</span>
      ) : (
        <>
          <span>{timeText}</span>
          <span style={{ opacity: 0.85, fontSize: '0.9em', fontWeight: 400 }}>
            &bull; {theme.label}
          </span>
        </>
      )}
    </div>
  );
};
