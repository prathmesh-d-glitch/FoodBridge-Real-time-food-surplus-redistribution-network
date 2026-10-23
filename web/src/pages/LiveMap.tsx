import React, { useState } from 'react';
import { RefreshCw, Truck, Utensils, HeartHandshake } from 'lucide-react';
import { useListings } from '../hooks/useListings';
import { MapView, MapMarker } from '../components/MapView';

export const LiveMapPage: React.FC = () => {
  const { listings, loading, refresh } = useListings();
  const [filter, setFilter] = useState<'all' | 'available' | 'claimed'>('all');

  const filteredListings = listings.filter((l) => {
    if (filter === 'all') return true;
    return l.status === filter;
  });

  // Assemble dynamic map markers
  const markers: MapMarker[] = [
    // Pre-seeded partner NGOs
    {
      id: 'ngo_1',
      lat: 12.9784,
      lng: 77.6408,
      title: 'Robin Hood Army Bangalore',
      description: 'Verified Shelter · Capacity: 250 kg',
      type: 'ngo',
    },
    {
      id: 'ngo_2',
      lat: 12.9352,
      lng: 77.6245,
      title: 'Koramangala Community Kitchen',
      description: 'Verified Shelter · Capacity: 150 kg',
      type: 'ngo',
    },
    {
      id: 'vol_1',
      lat: 12.9700,
      lng: 77.5900,
      title: 'Volunteer Arun Kumar',
      description: 'En-route for banquet pickup',
      type: 'volunteer',
    },
    // Dynamic listings
    ...filteredListings.map((l) => ({
      id: l.id,
      lat: l.location.latitude,
      lng: l.location.longitude,
      title: l.title,
      description: `${l.portions} portions (${l.quantity_kg}kg) · Safe until: ${new Date(l.safe_until).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`,
      type: 'donor' as const,
      portions: l.portions,
      safeUntil: l.safe_until,
    })),
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.025em', marginBottom: '3px' }}>
            Live Redistribution Map
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            Geospatial telemetry showing surplus food, recipient shelters, and courier routes
          </p>
        </div>

        <div className="segmented-nav">
          <button
            type="button"
            className={`segmented-nav-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({markers.length})
          </button>
          <button
            type="button"
            className={`segmented-nav-btn ${filter === 'available' ? 'active' : ''}`}
            onClick={() => setFilter('available')}
          >
            Available
          </button>
          <button
            type="button"
            className={`segmented-nav-btn ${filter === 'claimed' ? 'active' : ''}`}
            onClick={() => setFilter('claimed')}
          >
            In-Transit
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(400px, 1fr) 320px', gap: '18px' }}>
        <div>
          <MapView markers={markers} height="600px" />
        </div>

        {/* Live Network Sidebar */}
        <div className="apple-card" style={{ padding: '0', display: 'flex', flexDirection: 'column', height: '600px', overflow: 'hidden' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', borderBottom: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              Network Entities ({markers.length})
            </span>
            <button
              type="button"
              className="btn btn-tertiary"
              style={{ padding: '3px 8px', fontSize: '12px', minHeight: '26px' }}
              onClick={refresh}
            >
              <RefreshCw size={12} />
              <span>Sync</span>
            </button>
          </div>

          <div style={{ overflowY: 'auto', flex: 1 }}>
            {markers.map((m) => (
              <div
                key={m.id}
                style={{
                  padding: '12px 18px',
                  borderBottom: '1px solid var(--border-subtle)',
                  transition: 'background-color 0.12s ease',
                  cursor: 'default',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '3px' }}>
                  {m.type === 'donor' && <Utensils size={13} color="var(--accent-primary)" />}
                  {m.type === 'ngo' && <HeartHandshake size={13} color="var(--accent-blue)" />}
                  {m.type === 'volunteer' && <Truck size={13} color="var(--accent-orange)" />}
                  <span style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>
                    {m.title}
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4, margin: 0 }}>
                  {m.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
