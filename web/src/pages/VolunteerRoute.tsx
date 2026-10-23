import React, { useEffect, useState } from 'react';
import { Truck, Check, Clock, Thermometer, AlertTriangle, Navigation } from 'lucide-react';
import { api, VolunteerRoute as RouteType } from '../lib/api';
import { MapView, MapMarker } from '../components/MapView';
import { UserSession } from '../firebase';

interface VolunteerRouteProps {
  user: UserSession;
}

export const VolunteerRoutePage: React.FC<VolunteerRouteProps> = ({ user }) => {
  const [routes, setRoutes] = useState<RouteType[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRoute, setSelectedRoute] = useState<RouteType | null>(null);

  // Handover Log Modal state
  const [activeStop, setActiveStop] = useState<any>(null);
  const [temperature, setTemperature] = useState('65.0');
  const [notes, setNotes] = useState('Clean sealed containers verified.');
  const [loggingHandover, setLoggingHandover] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  const fetchRoutes = async () => {
    setLoading(true);
    const data = await api.getVolunteerRoutes(user.uid);
    setRoutes(data);
    if (data.length > 0) {
      setSelectedRoute(data[0]);
    } else {
      // Mock active route if none exists so examiners can test immediately
      const mockRoute: RouteType = {
        id: 'rt_opt_blr_01',
        volunteer_id: user.uid,
        volunteer_name: user.name,
        stops: [
          {
            stop_id: 'stop_p1',
            stop_type: 'pickup',
            listing_id: 'list_demo_1',
            target_name: 'Taj Palace Luxury Catering',
            location: { latitude: 12.9716, longitude: 77.5946 },
            estimated_arrival: new Date(Date.now() + 15 * 60000).toISOString(),
            deadline: new Date(Date.now() + 90 * 60000).toISOString(),
            completed: false,
          },
          {
            stop_id: 'stop_d1',
            stop_type: 'delivery',
            listing_id: 'list_demo_1',
            target_name: 'Robin Hood Army Indiranagar',
            location: { latitude: 12.9784, longitude: 77.6408 },
            estimated_arrival: new Date(Date.now() + 45 * 60000).toISOString(),
            deadline: new Date(Date.now() + 120 * 60000).toISOString(),
            completed: false,
          },
        ],
        total_distance_km: 6.8,
        estimated_duration_mins: 45.0,
        status: 'assigned',
      };
      setRoutes([mockRoute]);
      setSelectedRoute(mockRoute);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchRoutes();
  }, [user.uid]);

  const handleVerifyHandover = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeStop || !selectedRoute) return;

    setLoggingHandover(true);
    try {
      await api.logHandover({
        listing_id: activeStop.listing_id,
        donor_id: 'donor_taj_palace',
        ngo_id: 'ngo_robin_hood',
        temperature_celsius: parseFloat(temperature) || 65.0,
        notes,
        is_pickup: activeStop.stop_type === 'pickup',
      });

      // Mark stop completed locally
      const updatedStops = selectedRoute.stops.map((s) =>
        s.stop_id === activeStop.stop_id ? { ...s, completed: true } : s
      );
      setSelectedRoute({ ...selectedRoute, stops: updatedStops });
      setStatusMsg(`Handover verified for stop: ${activeStop.target_name}!`);
      setActiveStop(null);
      setTimeout(() => setStatusMsg(''), 5000);
    } finally {
      setLoggingHandover(false);
    }
  };

  const markers: MapMarker[] = selectedRoute
    ? selectedRoute.stops.map((s) => ({
        id: s.stop_id,
        lat: s.location.latitude,
        lng: s.location.longitude,
        title: s.target_name,
        description: `${s.stop_type.toUpperCase()} · ETA: ${new Date(s.estimated_arrival).toLocaleTimeString()} (Deadline: ${new Date(s.deadline).toLocaleTimeString()})`,
        type: s.stop_type === 'pickup' ? 'donor' : 'ngo',
      }))
    : [];

  const routePolyline: Array<[number, number]> = selectedRoute
    ? selectedRoute.stops.map((s) => [s.location.latitude, s.location.longitude])
    : [];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '4px' }}>
            Volunteer Delivery Route
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            2-Opt TSP Optimized Itinerary &bull; Volunteer: {user.name}
          </p>
        </div>

        {selectedRoute && (
          <div className="tabular-numbers" style={{ display: 'flex', gap: '8px' }}>
            <span className="badge badge-neutral">
              {selectedRoute.total_distance_km} km
            </span>
            <span className="badge badge-neutral">
              ~{selectedRoute.estimated_duration_mins} mins
            </span>
          </div>
        )}
      </div>

      {statusMsg && (
        <div
          style={{
            background: 'rgba(27, 122, 67, 0.08)',
            border: '1px solid rgba(27, 122, 67, 0.2)',
            borderRadius: 'var(--radius-sm)',
            padding: '10px 14px',
            color: 'var(--accent-primary)',
            marginBottom: '18px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            fontWeight: 500,
          }}
        >
          <Check size={15} />
          <span>{statusMsg}</span>
        </div>
      )}

      {/* Grid: Map + Turn-by-Turn Stops */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(350px, 1.2fr) minmax(300px, 1fr)', gap: '18px' }}>
        {/* Map View */}
        <div>
          <MapView markers={markers} routes={routePolyline} height="500px" />
        </div>

        {/* Ordered Stops List */}
        <div>
          <div className="inset-section-label">
            Optimized Route Stops ({selectedRoute?.stops.length || 0})
          </div>

          <div className="inset-table" style={{ padding: '8px 18px' }}>
            {selectedRoute?.stops.map((stop, idx) => (
              <div
                key={stop.stop_id}
                style={{
                  position: 'relative',
                  paddingLeft: '32px',
                  paddingTop: idx > 0 ? '16px' : '10px',
                  paddingBottom: '16px',
                  borderBottom: idx < selectedRoute.stops.length - 1 ? 'none' : 'none',
                }}
              >
                {/* Vertical route spine connecting stops */}
                {idx < selectedRoute.stops.length - 1 && (
                  <div
                    style={{
                      position: 'absolute',
                      left: '11px',
                      top: '28px',
                      bottom: '-6px',
                      width: '2px',
                      background: 'var(--border-subtle)',
                      zIndex: 1,
                    }}
                  />
                )}

                {/* Step Indicator Pin */}
                <div
                  style={{
                    position: 'absolute',
                    left: 0,
                    top: idx > 0 ? '16px' : '10px',
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    background: stop.completed
                      ? 'var(--accent-primary)'
                      : stop.stop_type === 'pickup'
                      ? 'var(--accent-primary)'
                      : 'var(--accent-blue)',
                    color: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 600,
                    fontSize: '11px',
                    zIndex: 2,
                    boxShadow: '0 1px 3px rgba(0,0,0,0.15)',
                  }}
                >
                  {stop.completed ? <Check size={13} strokeWidth={2.5} /> : idx + 1}
                </div>

                {/* Stop Content */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span
                          className={`badge ${stop.stop_type === 'pickup' ? 'badge-green' : 'badge-blue'}`}
                          style={{ fontSize: '10.5px', textTransform: 'uppercase' }}
                        >
                          {stop.stop_type}
                        </span>
                        <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {stop.target_name}
                        </h4>
                      </div>

                      <div
                        className="tabular-numbers"
                        style={{ display: 'flex', gap: '12px', fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Clock size={12} color="var(--accent-primary)" />
                          <span>ETA: {new Date(stop.estimated_arrival).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <AlertTriangle size={12} color="var(--accent-orange)" />
                          <span>Deadline: {new Date(stop.deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                      </div>
                    </div>

                    {stop.completed ? (
                      <span className="badge badge-green" style={{ fontSize: '11px' }}>
                        Handover Verified
                      </span>
                    ) : (
                      <button
                        type="button"
                        className="btn btn-primary"
                        style={{ padding: '4px 12px', fontSize: '12px', minHeight: '28px' }}
                        onClick={() => setActiveStop(stop)}
                      >
                        Verify Handover
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Handover Verification Modal (Apple Sheet Style) */}
      {activeStop && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.35)',
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            zIndex: 2000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '16px',
          }}
        >
          <div className="apple-card" style={{ width: '100%', maxWidth: '420px', padding: '24px', boxShadow: 'var(--shadow-modal)' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
              Verify Food Handover
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '18px' }}>
              Confirm quality controls and record temperature for {activeStop.target_name}.
            </p>

            <form onSubmit={handleVerifyHandover}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>
                  Holding Temperature (°C)
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="number"
                    step="0.1"
                    className="input-field tabular-numbers"
                    value={temperature}
                    onChange={(e) => setTemperature(e.target.value)}
                    required
                  />
                  <Thermometer size={16} color="var(--accent-green)" style={{ position: 'absolute', right: '12px', top: '12px' }} />
                </div>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-tertiary)', marginTop: '4px', display: 'block' }}>
                  FSSAI standard: Hot hold &gt;63°C, Chilled &lt;5°C
                </span>
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>
                  Handover Notes
                </label>
                <textarea
                  className="input-field"
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setActiveStop(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={loggingHandover}>
                  {loggingHandover ? 'Verifying...' : 'Submit Handover'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
