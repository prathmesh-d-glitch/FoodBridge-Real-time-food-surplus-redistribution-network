import React from 'react';
import { Plus, RefreshCw, Utensils } from 'lucide-react';
import { useListings } from '../hooks/useListings';
import { ListingCard } from '../components/ListingCard';
import { UserSession } from '../firebase';

interface DonorDashboardProps {
  user: UserSession;
  onNavigatePost: () => void;
}

export const DonorDashboard: React.FC<DonorDashboardProps> = ({ user, onNavigatePost }) => {
  const { listings, loading, refresh } = useListings();

  const donorListings = listings.filter((l) => l.donor_id === user.uid || user.role === 'admin');

  const totalPortions = donorListings.reduce((acc, curr) => acc + (curr.portions || 0), 0);
  const totalKg = donorListings.reduce((acc, curr) => acc + (curr.quantity_kg || 0), 0);

  return (
    <div>
      {/* View Header & Toolbar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.025em', marginBottom: '3px' }}>
            Surplus Postings
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            {user.name} &bull; Spoilage-aware food redistribution center
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button type="button" className="btn btn-secondary" onClick={refresh} title="Refresh data">
            <RefreshCw size={13} />
            <span>Refresh</span>
          </button>
          <button type="button" className="btn btn-primary" onClick={onNavigatePost}>
            <Plus size={14} />
            <span>Post Surplus</span>
          </button>
        </div>
      </div>

      {/* Glanceable Metrics Summary Bar */}
      {donorListings.length > 0 && (
        <div
          className="tabular-numbers"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px 20px',
            marginBottom: '22px',
            fontSize: '13px',
            color: 'var(--text-secondary)',
            boxShadow: 'var(--shadow-subtle)',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
            <div>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{donorListings.length}</span> active postings
            </div>
            <span style={{ width: '1px', height: '14px', background: 'var(--border-subtle)' }} />
            <div>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{totalPortions}</span> portions available
            </div>
            <span style={{ width: '1px', height: '14px', background: 'var(--border-subtle)' }} />
            <div>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{totalKg.toFixed(1)} kg</span> total weight
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-primary)', fontSize: '12px', fontWeight: 500 }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-primary)' }} />
            <span>All within safe consumption windows</span>
          </div>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-tertiary)', fontSize: '13px' }}>
          Loading surplus postings...
        </div>
      ) : donorListings.length === 0 ? (
        <div className="apple-card" style={{ padding: '48px 24px', textAlign: 'center', maxWidth: '480px', margin: '40px auto' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '50%',
              background: 'rgba(0, 0, 0, 0.04)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 14px',
              color: 'var(--text-secondary)',
            }}
          >
            <Utensils size={18} />
          </div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
            No Active Postings
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '20px', lineHeight: 1.5 }}>
            Post surplus banquet or restaurant food to begin matching with nearby verified shelters.
          </p>
          <button type="button" className="btn btn-primary" onClick={onNavigatePost}>
            <Plus size={14} />
            <span>Post Food Surplus</span>
          </button>
        </div>
      ) : (
        <div>
          <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '12px' }}>
            Active Batches ({donorListings.length})
          </div>

          <div className="grid-cols-auto">
            {donorListings.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
