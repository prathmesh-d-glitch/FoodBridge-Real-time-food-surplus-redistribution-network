import React, { useEffect, useState } from 'react';

interface ImpactCounterProps {
  value: number;
  label: string;
  icon: React.ReactNode;
  unit?: string;
  color?: string;
}

export const ImpactCounter: React.FC<ImpactCounterProps> = ({
  value,
  label,
  icon,
  unit = '',
}) => {
  const [displayVal, setDisplayVal] = useState(0);

  useEffect(() => {
    let start = displayVal;
    const end = value;
    if (start === end) return;

    const duration = 1000;
    const stepTime = 30;
    const steps = duration / stepTime;
    const increment = (end - start) / steps;

    const timer = setInterval(() => {
      start += increment;
      if ((increment > 0 && start >= end) || (increment < 0 && start <= end)) {
        setDisplayVal(end);
        clearInterval(timer);
      } else {
        setDisplayVal(Math.round(start * 10) / 10);
      }
    }, stepTime);

    return () => clearInterval(timer);
  }, [value]);

  return (
    <div className="apple-card" style={{ padding: '20px 22px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
        <span style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
          {label}
        </span>
        <div style={{ color: 'var(--text-tertiary)' }}>
          {icon}
        </div>
      </div>
      <div className="tabular-numbers" style={{ fontSize: '2.1rem', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.1, letterSpacing: '-0.025em' }}>
        {displayVal.toLocaleString()} {unit && <span style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', fontWeight: 400 }}>{unit}</span>}
      </div>
    </div>
  );
};
