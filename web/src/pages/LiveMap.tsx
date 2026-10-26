import React, { useState } from 'react';
import {
  RefreshCw,
  Truck,
  Utensils,
  HeartHandshake,
  Navigation,
  Loader2,
  MapPin,
  CheckCircle2,
} from 'lucide-react';
import { useListings } from '../hooks/useListings';
import { MapView, MapMarker } from '../components/MapView';
import {
  getCurrentLocationWithPlaceName,
  formatCoordinates,
  LocationResult,
  BANGALORE_CENTER,
} from '../lib/geo';

export const LiveMapPage: React.FC = () => {
  const { listings, loading, refresh } = useListings();
  const [filter, setFilter] = useState<'all' | 'available' | 'claimed'>('all');
  const [userLocation, setUserLocation] = useState<LocationResult | null>(null);
  const [locating, setLocating] = useState(false);
  const [mapCenter, setMapCenter] = useState<[number, number]>(BANGALORE_CENTER);
  const [locMessage, setLocMessage] = useState<string | null>(null);

  const filteredListings = listings.filter((l) => {
    if (filter === 'all') return true;
    return l.status === filter;
  });

  const handleLocateMe = async () => {
    setLocating(true);
    setLocMessage(null);
    try {
      const loc = await getCurrentLocationWithPlaceName();
      setUserLocation(loc);
      setMapCenter([loc.latitude, loc.longitude]);
      setLocMessage(`Located: ${loc.placeName} (${formatCoordinates(loc.latitude, loc.longitude)})`);
      setTimeout(() => setLocMessage(null), 5000);
    } catch (err: any) {
      alert(err.message || 'Could not access device GPS.');
    } finally {
      setLocating(false);
    }
  };

  // Assemble dynamic map markers
  const markers: MapMarker[] = [
    // If user clicked Locate Me, pin their position
    ...(userLocation
      ? [
          {
            id: 'user_live_spot',
            lat: userLocation.latitude,
            lng: userLocation.longitude,
            title: `📍 My Location: ${userLocation.placeName}`,
            description: `${userLocation.formattedAddress} · Accurate to ${Math.round(userLocation.accuracy || 15)}m`,
            type: 'ngo' as const,
          },
        ]
      : []),
    // Pre-seeded partner NGOs
    {
      id: 'ngo_1',
      lat: 12.9784,
      lng: 77.6408,
      title: 'Robin Hood Army Bangalore',
      description: 'Verified Shelter · Capacity: 250 kg · Indiranagar',
      type: 'ngo',
    },
    {
      id: 'ngo_2',
      lat: 12.9352,
      lng: 77.6245,
      title: 'Koramangala Community Kitchen',
      description: 'Verified Shelter · Capacity: 150 kg · Koramangala 4th Block',
      type: 'ngo',
    },
    {
      id: 'vol_1',
      lat: 12.9700,
      lng: 77.5900,
      title: 'Volunteer Courier Arun Kumar',
      description: 'En-route for banquet pickup · MG Road',
      type: 'volunteer',
    },
    // Dynamic listings
    ...filteredListings.map((l) => ({
      id: l.id,
      lat: l.location.latitude,
      lng: l.location.longitude,
      title: `${l.title} (${l.location.address || 'Bengaluru'})`,
      description: `${l.portions} portions (${l.quantity_kg}kg) · Safe until: ${new Date(l.safe_until).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`,
      type: 'donor' as const,
      portions: l.portions,
      safeUntil: l.safe_until,
    })),
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.025em', marginBottom: '3px' }}>
            Live Redistribution Map
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            Geospatial telemetry showing surplus food, recipient shelters, and courier routes
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Locate Me Button */}
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleLocateMe}
            disabled={locating}
            style={{
              padding: '6px 12px',
              fontSize: '12.5px',
              fontWeight: 600,
              color: 'var(--accent-primary)',
              borderColor: 'rgba(27, 122, 67, 0.3)',
            }}
          >
            {locating ? (
              <>
                <Loader2 size={13} className="spin" />
                <span>Locating...</span>
              </>
            ) : (
              <>
                <Navigation size={13} />
                <span>Get My Location</span>
              </>
            )}
          </button>

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
      </div>

      {locMessage && (
        <div
          style={{
            background: 'rgba(27, 122, 67, 0.08)',
            border: '1px solid rgba(27, 122, 67, 0.25)',
            borderRadius: '8px',
            padding: '8px 14px',
            color: 'var(--accent-primary)',
            fontSize: '12.5px',
            marginBottom: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <CheckCircle2 size={14} />
          <span>{locMessage}</span>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(400px, 1fr) 320px', gap: '18px' }}>
        <div>
          <MapView markers={markers} center={mapCenter} zoom={userLocation ? 14 : 12} height="600px" />
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
            {userLocation && (
              <div
                style={{
                  padding: '12px 18px',
                  background: 'rgba(27, 122, 67, 0.06)',
                  borderBottom: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                  <MapPin size={13} color="var(--accent-primary)" />
                  <span style={{ fontWeight: 600, fontSize: '12.5px', color: 'var(--accent-primary)' }}>
                    My Current Spot
                  </span>
                </div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {userLocation.placeName}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  {formatCoordinates(userLocation.latitude, userLocation.longitude)}
                </div>
              </div>
            )}

            {markers
              .filter((m) => m.id !== 'user_live_spot')
              .map((m) => (
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
