import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Check } from 'lucide-react';

interface ScoreBreakdown {
  time_feasibility: number;
  proximity: number;
  capacity_fit: number;
  dietary_match: number;
  reliability: number;
  need_urgency: number;
  total_score: number;
  explanation: string;
}

interface MatchExplainerProps {
  score: number;
  breakdown: ScoreBreakdown;
  rank: number;
}

export const MatchExplainer: React.FC<MatchExplainerProps> = ({ score, breakdown, rank }) => {
  const [expanded, setExpanded] = useState(false);

  const factors = [
    { label: 'Time Feasibility', weight: '30%', val: breakdown.time_feasibility },
    { label: 'Proximity', weight: '25%', val: breakdown.proximity },
    { label: 'Capacity Fit', weight: '15%', val: breakdown.capacity_fit },
    { label: 'Dietary Match', weight: '10%', val: breakdown.dietary_match },
    { label: 'Reliability', weight: '15%', val: breakdown.reliability },
    { label: 'Need Urgency', weight: '5%', val: breakdown.need_urgency },
  ];

  return (
    <div
      style={{
        marginTop: '12px',
        background: 'rgba(0, 0, 0, 0.025)',
        borderRadius: 'var(--radius-sm)',
        padding: '12px 14px',
      }}
    >
      <div
        onClick={() => setExpanded(!expanded)}
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', userSelect: 'none' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="tabular-numbers" style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
            {(score * 100).toFixed(0)}% Compatibility Fit
          </span>
          <span style={{ fontSize: '11.5px', color: 'var(--accent-primary)', fontWeight: 500 }}>
            &bull; Rank #{rank} Choice
          </span>
        </div>
        <button
          type="button"
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: '3px',
            cursor: 'pointer',
            fontSize: '12px',
            fontFamily: 'inherit',
          }}
        >
          {expanded ? 'Hide Breakdown' : 'Explain Score'}
          {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        </button>
      </div>

      {expanded && (
        <div style={{ marginTop: '12px', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '12px', lineHeight: 1.45 }}>
            {breakdown.explanation}
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {factors.map((f, i) => (
              <div key={i}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11.5px', color: 'var(--text-secondary)', marginBottom: '3px' }}>
                  <span>{f.label} <span style={{ color: 'var(--text-tertiary)' }}>({f.weight})</span></span>
                  <span className="tabular-numbers" style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{(f.val * 100).toFixed(0)}%</span>
                </div>
                <div style={{ width: '100%', height: '3.5px', background: 'rgba(0, 0, 0, 0.08)', borderRadius: '2px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${Math.min(100, f.val * 100)}%`,
                      height: '100%',
                      background: 'var(--accent-primary)',
                      borderRadius: '2px',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '10px', display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11.5px', color: 'var(--accent-primary)', fontWeight: 500 }}>
            <Check size={13} />
            <span>Passed Spoilage Feasibility Constraints</span>
          </div>
        </div>
      )}
    </div>
  );
};
