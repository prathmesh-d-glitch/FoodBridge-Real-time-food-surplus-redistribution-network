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
import { useLanguage } from '../i18n/context';

interface ImpactDashboardProps {
  user?: UserSession;
}

export const ImpactDashboard: React.FC<ImpactDashboardProps> = ({ user }) => {
  const { t } = useLanguage();
  const [metrics, setMetrics] = useState<ImpactMetrics>(() => {
    try {
      const saved = localStorage.getItem('foodbridge_cached_impact');
      if (saved) return JSON.parse(saved);
    } catch {}
    return {
      total_kg_diverted: 142.5,
      total_meals_saved: 410,
      total_co2e_avoided_kg: 356.25,
      completed_deliveries: 8,
      co2e_factor_used: 2.5,
    };
  });

  const [forecast, setForecast] = useState<any>(null);
  const [selectedWeekday, setSelectedWeekday] = useState(4); // Friday
  const [selectedHour, setSelectedHour] = useState(22);      // 10 PM

  useEffect(() => {
    const loadData = async () => {
      const imp = await api.getImpact();
      if (imp.completed_deliveries > 0) {
        setMetrics(imp);
        localStorage.setItem('foodbridge_cached_impact', JSON.stringify(imp));
      }
      const fc = await api.getForecast(selectedWeekday, selectedHour);
      setForecast(fc);
    };
    loadData();
  }, [selectedWeekday, selectedHour]);

  const weekdays: string[] = t.common.weekdays as string[];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '4px' }}>
            {t.impact_page.title}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            {t.impact_page.subtitle}
          </p>
        </div>

        <a
          href={api.getCertificateUrl(user?.uid || 'donor_taj_palace')}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-secondary"
          style={{ textDecoration: 'none' }}
        >
          <Download size={14} />
          <span>{t.impact_page.download_csr}</span>
        </a>
      </div>

      {/* Impact Counters Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        <ImpactCounter
          value={metrics.total_meals_saved}
          label={t.impact_page.meals_saved}
          icon={<Utensils size={17} />}
        />
        <ImpactCounter
          value={metrics.total_kg_diverted}
          label={t.impact_page.food_diverted}
          icon={<Scale size={17} />}
          unit="kg"
        />
        <ImpactCounter
          value={metrics.total_co2e_avoided_kg}
          label={t.impact_page.co2e_avoided}
          icon={<Leaf size={17} />}
          unit="kg"
        />
        <ImpactCounter
          value={metrics.completed_deliveries}
          label={t.impact_page.rescues_completed}
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
                {t.impact_page.csr_title}
              </h3>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '12.5px', lineHeight: 1.48, marginBottom: '20px' }}>
              {t.impact_page.csr_desc}
            </p>

            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '14px', marginBottom: '20px' }}>
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em', marginBottom: '2px' }}>
                  {t.impact_page.beneficiary}
                </div>
                <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {user?.name}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12.5px', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)', paddingTop: '8px' }}>
                <span>{t.impact_page.certified_period}</span>
                <strong style={{ color: 'var(--text-primary)' }}>{t.common.october_2026}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12.5px', color: 'var(--text-secondary)', marginTop: '8px' }}>
                <span>{t.impact_page.ghg_standard}</span>
                <strong style={{ color: 'var(--text-primary)' }}>UN SDG 12.3</strong>
              </div>
            </div>
          </div>

          <a
            href={api.getCertificateUrl(user?.uid || 'donor_taj_palace')}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
            style={{ width: '100%', textDecoration: 'none' }}
          >
            <Download size={13} />
            <span>{t.impact_page.generate_pdf}</span>
          </a>
        </div>

        {/* Predictive Surplus Forecasting Engine */}
        <div className="apple-card" style={{ padding: '22px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <TrendingUp size={16} color="var(--accent-blue)" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {t.impact_page.forecast_title}
            </h3>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '12.5px', lineHeight: 1.48, marginBottom: '18px' }}>
            {t.impact_page.forecast_desc}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '18px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 500, marginBottom: '5px' }}>
                {t.impact_page.day_of_week}
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
                {t.impact_page.time_window}
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
                  {t.impact_page.projected_surplus}
                </span>
                <span className="badge badge-neutral" style={{ fontSize: '11px' }}>{(forecast.confidence_score * 100).toFixed(0)}% {t.impact_page.confidence}</span>
              </div>

              <div className="tabular-numbers" style={{ fontSize: '1.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px', letterSpacing: '-0.02em' }}>
                {forecast.predicted_surplus_kg} <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 400 }}>kg</span>
              </div>
              <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                {t.impact_page.approximately} <strong style={{ color: 'var(--text-primary)' }}>{forecast.expected_portions} {t.impact_page.meals_saved.toLowerCase()}</strong> {t.impact_page.meals_expected}
              </div>

              <div style={{ fontSize: '11.5px', color: 'var(--text-tertiary)', lineHeight: 1.4 }}>
                {t.impact_page.model}: {forecast.method} &bull; Multiplier: {forecast.seasonal_multiplier}x
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
