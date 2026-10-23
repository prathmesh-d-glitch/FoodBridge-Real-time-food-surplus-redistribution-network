import React from 'react';
import { Sparkles, MapPin } from 'lucide-react';
import { DonorListing } from '../lib/api';
import { FreshnessClock } from './FreshnessClock';
import { TrustBadge } from './TrustBadge';

interface ListingCardProps {
  listing: DonorListing;
  onSelect?: (listing: DonorListing) => void;
}

export const ListingCard: React.FC<ListingCardProps> = ({ listing, onSelect }) => {
  return (
    <div
      className={`apple-card ${onSelect ? 'apple-card-interactive' : ''}`}
      onClick={() => onSelect && onSelect(listing)}
      style={{
        padding: '18px 20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gap: '14px',
      }}
    >
      <div>
        {/* Category Eyebrow & Glanceable Clock */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            {listing.category.replace('_', ' ')}
          </span>
          <FreshnessClock safeUntil={listing.safe_until} size="sm" />
        </div>

        {/* Title */}
        <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.3, marginBottom: '4px' }}>
          {listing.title}
        </h3>

        {/* Location & Donor */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12.5px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
          <MapPin size={12} color="var(--text-tertiary)" />
          <span>{listing.donor_name} &bull; {listing.location.address || 'Bangalore'}</span>
        </div>

        {/* Description */}
        {listing.description && (
          <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginBottom: '12px', lineHeight: 1.45 }}>
            {listing.description}
          </p>
        )}

        {/* Tabular Food Specifications Bar */}
        <div
          className="tabular-numbers"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: 'var(--text-secondary)',
            marginBottom: '10px',
            flexWrap: 'wrap',
          }}
        >
          <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
            {listing.portions} portions
          </span>
          <span style={{ color: 'var(--border-subtle)' }}>&bull;</span>
          <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
            {listing.quantity_kg} kg
          </span>
          <span style={{ color: 'var(--border-subtle)' }}>&bull;</span>
          <span style={{ textTransform: 'capitalize' }}>{listing.dietary_type}</span>
          <span style={{ color: 'var(--border-subtle)' }}>&bull;</span>
          <span>{listing.storage_condition.replace('_', ' ')}</span>
        </div>

        {/* Gemini Vision AI Verification Strip */}
        {listing.photo_analysis && (
          <div
            style={{
              background: 'rgba(0, 0, 0, 0.025)',
              borderRadius: 'var(--radius-xs)',
              padding: '7px 10px',
              fontSize: '11.5px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-primary)', fontWeight: 500 }}>
              <span style={{ color: 'var(--accent-primary)' }}>&bull;</span>
              <span>Inspection Verified ({(listing.photo_analysis.confidence * 100).toFixed(0)}% confidence)</span>
            </div>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', margin: '2px 0 0' }}>
              {listing.photo_analysis.safety_flags.length > 0
                ? listing.photo_analysis.safety_flags.join(', ')
                : 'Packaging sealed and temperature compliant.'}
            </p>
          </div>
        )}
      </div>

      {/* Footer Metadata */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderTop: '1px solid var(--border-subtle)',
          paddingTop: '12px',
          marginTop: '6px',
        }}
      >
        <TrustBadge verified={true} reliabilityScore={0.96} />
        <span
          className={`badge ${
            listing.status === 'available'
              ? 'badge-green'
              : listing.status === 'offered'
              ? 'badge-amber'
              : 'badge-neutral'
          }`}
          style={{ textTransform: 'capitalize' }}
        >
          {listing.status === 'available' ? 'Available for Pickup' : listing.status}
        </span>
      </div>
    </div>
  );
};
