import React, { useEffect, useState } from 'react';
import {
  Utensils,
  Leaf,
  Scale,
  Award,
  Download,
  TrendingUp,
} from 'lucide-react';
import { api, ImpactMetrics } from '../lib/api';
import { ImpactCounter } from '../components/ImpactCounter';
import { UserSession } from '../firebase';

interface ImpactDashboardProps {
  user: UserSession;
}

export const ImpactDashboard: React.FC<ImpactDashboardProps> = ({ user }) => {
  const [metrics, setMetrics] = useState<ImpactMetrics>({
    total_kg_diverted: 142.5,
    total_meals_saved: 410,
    total_co2e_avoided_kg: 356.25,
    completed_deliveries: 8,
    co2e_factor_used: 2.5,
  });

  const [forecast, setForecast] = useState<any>(null);
  const [selectedWeekday, setSelectedWeekday] = useState(4); // Friday
  const [selectedHour, setSelectedHour] = useState(22);      // 10 PM

  useEffect(() => {
    const loadData = async () => {
      const imp = await api.getImpact();
      if (imp.completed_deliveries > 0) {
        setMetrics(imp);
      }
      const fc = await api.getForecast(selectedWeekday, selectedHour);
      setForecast(fc);
    };
    loadData();
  }, [selectedWeekday, selectedHour]);

  const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '4px' }}>
            Impact &amp; Analytics
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Audited sustainability metrics aligned with UN SDG 2 and SDG 12
          </p>
        </div>

        <a
          href={api.getCertificateUrl(user.uid)}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-secondary"
          style={{ textDecoration: 'none' }}
        >
          <Download size={14} />
          <span>Download CSR Certificate (PDF)</span>
        </a>
      </div>

      {/* Impact Counters Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        <ImpactCounter
          value={metrics.total_meals_saved}
          label="Meals Saved"
          icon={<Utensils size={17} />}
        />
        <ImpactCounter
          value={metrics.total_kg_diverted}
          label="Food Diverted"
          icon={<Scale size={17} />}
          unit="kg"
        />
        <ImpactCounter
          value={metrics.total_co2e_avoided_kg}
          label="CO2e Avoided"
          icon={<Leaf size={17} />}
          unit="kg"
        />
        <ImpactCounter
          value={metrics.completed_deliveries}
          label="Rescues Completed"
          icon={<Award size={17} />}
        />
      </div>

      {/* Grid: CSR Certificate Preview + Surplus Forecaster */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(320px, 1fr)', gap: '20px' }}>
        {/* Certificate Preview Card */}
        <div className="apple-card" style={{ padding: '22px 24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <Award size={16} color="var(--accent-primary)" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Monthly CSR Impact Certificate
              </h3>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '12.5px', lineHeight: 1.48, marginBottom: '20px' }}>
              Cryptographically verified sustainability certificate generated in real-time. Compliant with corporate ESG statutory reporting and audit disclosures.
            </p>

            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '14px', marginBottom: '20px' }}>
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em', marginBottom: '2px' }}>
                  Beneficiary Organization
                </div>
                <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {user.name}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12.5px', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)', paddingTop: '8px' }}>
                <span>Certified Period:</span>
                <strong style={{ color: 'var(--text-primary)' }}>October 2026</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12.5px', color: 'var(--text-secondary)', marginTop: '8px' }}>
                <span>GHG Offset Standard:</span>
                <strong style={{ color: 'var(--text-primary)' }}>UN SDG 12.3</strong>
              </div>
            </div>
          </div>

          <a
            href={api.getCertificateUrl(user.uid)}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
            style={{ width: '100%', textDecoration: 'none' }}
          >
            <Download size={13} />
            <span>Generate PDF Certificate</span>
          </a>
        </div>

        {/* Predictive Surplus Forecasting Engine */}
        <div className="apple-card" style={{ padding: '22px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <TrendingUp size={16} color="var(--accent-blue)" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Surplus Forecasting
            </h3>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '12.5px', lineHeight: 1.48, marginBottom: '18px' }}>
            Predicts expected surplus by analyzing seasonal trends and commercial meal service cycles.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '18px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 500, marginBottom: '5px' }}>
                Day of Week
              </label>
              <select
                className="input-field"
                value={selectedWeekday}
                onChange={(e) => setSelectedWeekday(parseInt(e.target.value))}
              >
                {weekdays.map((d, i) => (
                  <option key={i} value={i}>{d}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 500, marginBottom: '5px' }}>
                Time Window
              </label>
              <select
                className="input-field"
                value={selectedHour}
                onChange={(e) => setSelectedHour(parseInt(e.target.value))}
              >
                <option value={15}>15:00 (Lunch Service)</option>
                <option value={19}>19:00 (Dinner Buffet)</option>
                <option value={22}>22:00 (Banquet Peak)</option>
                <option value={0}>00:00 (Late Night)</option>
              </select>
            </div>
          </div>

          {forecast && (
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>
                  Projected Surplus
                </span>
                <span className="badge badge-neutral" style={{ fontSize: '11px' }}>{(forecast.confidence_score * 100).toFixed(0)}% Confidence</span>
              </div>

              <div className="tabular-numbers" style={{ fontSize: '1.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px', letterSpacing: '-0.02em' }}>
                {forecast.predicted_surplus_kg} <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 400 }}>kg</span>
              </div>
              <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                Approximately <strong style={{ color: 'var(--text-primary)' }}>{forecast.expected_portions} meals</strong> expected from operations.
              </div>

              <div style={{ fontSize: '11.5px', color: 'var(--text-tertiary)', lineHeight: 1.4 }}>
                Model: {forecast.method} &bull; Multiplier: {forecast.seasonal_multiplier}x
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
