import React, { useState } from 'react';
import {
  Sparkles,
  Upload,
  ArrowLeft,
  AlertTriangle,
  MapPin,
  Navigation,
  Loader2,
  CheckCircle2,
  Compass,
} from 'lucide-react';
import { api } from '../lib/api';
import { UserSession } from '../firebase';
import {
  formatCoordinates,
  getCurrentLocationWithPlaceName,
  LocationResult,
  PRESET_LOCATIONS,
} from '../lib/geo';

interface PostSurplusProps {
  user: UserSession;
  onSuccess: () => void;
  onCancel: () => void;
}

export const PostSurplus: React.FC<PostSurplusProps> = ({ user, onSuccess, onCancel }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('cooked_meals');
  const [storageCondition, setStorageCondition] = useState('hot_hold');
  const [dietaryType, setDietaryType] = useState('veg');
  const [quantityKg, setQuantityKg] = useState(25.0);
  const [portions, setPortions] = useState(60);
  const [photoBase64, setPhotoBase64] = useState<string | null>(null);

  // Auto-detect Gwalior donor location
  const isGwaliorDonor =
    user.name?.toLowerCase().includes('gwalior') ||
    user.email?.toLowerCase().includes('gwalior') ||
    user.organization?.toLowerCase().includes('gwalior');

  // Location state
  const [placeName, setPlaceName] = useState(
    isGwaliorDonor
      ? 'Jayaji Chowk, Lashkar, Gwalior, Madhya Pradesh'
      : 'Palace Grounds, MG Road, Bengaluru'
  );
  const [latitude, setLatitude] = useState(isGwaliorDonor ? 26.2045 : 12.9716);
  const [longitude, setLongitude] = useState(isGwaliorDonor ? 78.1560 : 77.5946);
  const [locating, setLocating] = useState(false);
  const [locationSuccess, setLocationSuccess] = useState(isGwaliorDonor);
  const [locationStatusText, setLocationStatusText] = useState<string | null>(
    isGwaliorDonor ? 'Auto-set to Gwalior Operating Area' : null
  );
  const [locationError, setLocationError] = useState<string | null>(null);

  // Gemini AI Analysis state
  const [analyzing, setAnalyzing] = useState(false);
  const [aiResult, setAiResult] = useState<any>(null);
  const [aiError, setAiError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        const b64 = reader.result as string;
        setPhotoBase64(b64);
        triggerAiAnalysis(b64);
      };
      reader.readAsDataURL(file);
    }
  };

  const triggerAiAnalysis = async (b64: string) => {
    setAnalyzing(true);
    setAiError(null);
    setAiResult(null);
    try {
      const res = await api.analyzePhoto(b64, title || 'Catering surplus');
      if (res && res.food_type) {
        setAiResult(res);
        if (res.estimated_portions) {
          setPortions(res.estimated_portions);
        }
      } else {
        setAiError('Gemini AI returned no result. Check that listing-service is running.');
      }
    } catch (err: any) {
      console.error(err);
      // 503 = Gemini API key missing or call failed
      if (err?.status === 503 || err?.response?.status === 503) {
        setAiError('Gemini AI unavailable — GEMINI_API_KEY not set or invalid.');
      } else {
        setAiError('Could not reach listing-service (port 8001). Ensure dev_servers.py is running.');
      }
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGetLocation = async () => {
    setLocating(true);
    setLocationError(null);
    setLocationStatusText('Querying browser GPS & reverse geocoding place name...');

    try {
      const loc: LocationResult = await getCurrentLocationWithPlaceName();
      setLatitude(loc.latitude);
      setLongitude(loc.longitude);
      setPlaceName(loc.formattedAddress || loc.placeName);
      setLocationSuccess(true);
      setLocationStatusText(
        `Acquired: ${loc.placeName} (${formatCoordinates(loc.latitude, loc.longitude)})`
      );
    } catch (err: any) {
      setLocationError(err.message || 'Unable to retrieve location from device.');
      setLocationStatusText(null);
    } finally {
      setLocating(false);
    }
  };

  const handleApplyPreset = (preset: LocationResult) => {
    setLatitude(preset.latitude);
    setLongitude(preset.longitude);
    setPlaceName(preset.formattedAddress);
    setLocationSuccess(true);
    setLocationError(null);
    setLocationStatusText(`Selected Preset: ${preset.placeName}`);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title) {
      setErrorMsg('Please enter a descriptive food title.');
      return;
    }

    if (!placeName) {
      setErrorMsg('Please specify the pickup place name or address.');
      return;
    }

    setSubmitting(true);
    setErrorMsg('');

    try {
      const payload = {
        title,
        description,
        category,
        storage_condition: storageCondition,
        dietary_type: dietaryType,
        quantity_kg: Number(quantityKg),
        portions: Number(portions),
        prepared_at: new Date().toISOString(),
        location: {
          latitude: Number(latitude),
          longitude: Number(longitude),
          address: placeName,
        },
        photo_base64: photoBase64,
      };

      await api.createListing(payload, user.token);
      onSuccess();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to post surplus listing');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '760px', margin: '0 auto', paddingBottom: '32px' }}>
      {/* Header & Back Link */}
      <div style={{ marginBottom: '20px' }}>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onCancel}
          style={{ marginBottom: '14px' }}
        >
          <ArrowLeft size={13} />
          <span>Surplus Dashboard</span>
        </button>

        <h2 style={{ fontSize: '1.55rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.025em', marginBottom: '4px' }}>
          Post Food Surplus
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
          Real-time matching engine computes safe expiration windows and dispatches cascading offers immediately.
        </p>
      </div>

      {errorMsg && (
        <div
          style={{
            background: 'rgba(215, 0, 21, 0.08)',
            border: '1px solid rgba(215, 0, 21, 0.2)',
            borderRadius: 'var(--radius-sm)',
            padding: '10px 14px',
            color: 'var(--accent-red)',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
          }}
        >
          <AlertTriangle size={15} />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Section 1: Food Photo & AI Inspection */}
        <div style={{ marginBottom: '22px' }}>
          <div className="inset-section-label">
            Photo &amp; Quality Inspection
          </div>
          <div className="apple-card" style={{ padding: '20px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: photoBase64 ? '180px 1fr' : '1fr', gap: '20px' }}>
              {photoBase64 ? (
                <div>
                  <img
                    src={photoBase64}
                    alt="Uploaded food"
                    style={{
                      width: '100%',
                      height: '140px',
                      objectFit: 'cover',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  />
                  <label
                    className="btn btn-secondary"
                    style={{ marginTop: '8px', width: '100%', textAlign: 'center', cursor: 'pointer', fontSize: '12px', padding: '6px' }}
                  >
                    Replace Photo
                    <input type="file" accept="image/*" onChange={handlePhotoUpload} style={{ display: 'none' }} />
                  </label>
                </div>
              ) : (
                <label
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1.5px dashed var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '30px 16px',
                    cursor: 'pointer',
                    background: 'rgba(0, 0, 0, 0.02)',
                    transition: 'border-color 0.15s ease',
                  }}
                >
                  <Upload size={24} color="var(--accent-primary)" style={{ marginBottom: '8px' }} />
                  <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '3px' }}>
                    Upload Food Batch Photo
                  </span>
                  <span style={{ fontSize: '11.5px', color: 'var(--text-tertiary)' }}>
                    Gemini Multimodal AI will inspect freshness and estimate portion counts
                  </span>
                  <input type="file" accept="image/*" onChange={handlePhotoUpload} style={{ display: 'none' }} />
                </label>
              )}

              {/* AI Analysis Result Card */}
              {analyzing ? (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '10px',
                    padding: '24px',
                    background: 'rgba(27, 122, 67, 0.04)',
                    borderRadius: 'var(--radius-sm)',
                  }}
                >
                  <Sparkles size={16} color="var(--accent-primary)" className="spin" />
                  <span style={{ fontSize: '13px', color: 'var(--accent-primary)', fontWeight: 500 }}>
                    Gemini 1.5 Flash analyzing visual spoilage indicators...
                  </span>
                </div>
              ) : aiError ? (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '16px',
                    background: 'rgba(215, 0, 21, 0.06)',
                    border: '1px solid rgba(215, 0, 21, 0.15)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '12px',
                    color: 'var(--accent-red)',
                  }}
                >
                  <AlertTriangle size={14} />
                  <span>{aiError}</span>
                </div>
              ) : aiResult ? (
                <div
                  style={{
                    padding: '16px',
                    background: 'rgba(27, 122, 67, 0.05)',
                    border: '1px solid rgba(27, 122, 67, 0.2)',
                    borderRadius: 'var(--radius-sm)',
                  }}
                >
                  {/* Gemini AI Badge */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
                    <Sparkles size={14} color="var(--accent-primary)" />
                    <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {aiResult.source === 'gemini' ? 'Gemini AI' : 'Rule-Based'}
                    </span>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      background: aiResult.confidence >= 0.85 ? 'rgba(27,122,67,0.15)' : 'rgba(200,140,0,0.13)',
                      color: aiResult.confidence >= 0.85 ? 'var(--accent-primary)' : '#a07000',
                      padding: '2px 8px',
                      borderRadius: '20px',
                      border: `1px solid ${aiResult.confidence >= 0.85 ? 'rgba(27,122,67,0.25)' : 'rgba(200,140,0,0.2)'}`,
                    }}>
                      {Math.round(aiResult.confidence * 100)}% confidence
                    </span>
                  </div>
                  <div style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
                    {aiResult.food_type}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px', display: 'flex', gap: '16px' }}>
                    <span>🕒 Shelf life: <strong>{aiResult.shelf_life_hours_hint}h</strong></span>
                    <span>🍽 Portions: <strong>{aiResult.estimated_portions}</strong> (auto-filled)</span>
                  </div>
                  {aiResult.safety_flags?.length > 0 && (
                    <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                      {aiResult.safety_flags.map((flag: string, i: number) => (
                        <span key={i} style={{ fontSize: '11px', background: 'rgba(27, 122, 67, 0.12)', color: 'var(--accent-primary)', padding: '2px 7px', borderRadius: '4px' }}>
                          ✓ {flag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          </div>
        </div>

        {/* Section 2: Core Details */}
        <div style={{ marginBottom: '22px' }}>
          <div className="inset-section-label">
            Food Specifications
          </div>
          <div className="apple-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '5px' }}>
                Batch Title *
              </label>
              <input
                type="text"
                required
                className="input-field"
                placeholder="e.g. 50 Portions Paneer Butter Masala &amp; Jeera Rice"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '5px' }}>
                Description &amp; Preparation Details
              </label>
              <textarea
                className="input-field"
                rows={2}
                placeholder="Cooked at 1:30 PM for lunch banquet, kept strictly in hot-hold bain-marie at 68°C."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '5px' }}>
                  Category (Determines Safe Window)
                </label>
                <select className="input-field" value={category} onChange={(e) => setCategory(e.target.value)}>
                  <option value="cooked_meals">Cooked Meals (4 hrs hot / 3 hrs ambient)</option>
                  <option value="bakery_bread">Bakery &amp; Breads (36 hrs)</option>
                  <option value="raw_produce">Raw Produce (24 hrs)</option>
                  <option value="dairy">Dairy Products (12 hrs chilled)</option>
                  <option value="packaged_goods">Packaged Goods (72 hrs)</option>
                  <option value="desserts">Desserts &amp; Sweets (16 hrs)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '5px' }}>
                  Storage Condition
                </label>
                <select className="input-field" value={storageCondition} onChange={(e) => setStorageCondition(e.target.value)}>
                  <option value="hot_hold">Hot Hold (&gt;63°C Bain-Marie)</option>
                  <option value="ambient">Ambient (Room Temperature)</option>
                  <option value="chilled">Chilled / Refrigerated (0-4°C)</option>
                  <option value="frozen">Frozen (&lt;-18°C)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '5px' }}>
                  Dietary Type
                </label>
                <select className="input-field" value={dietaryType} onChange={(e) => setDietaryType(e.target.value)}>
                  <option value="veg">Vegetarian (Strict)</option>
                  <option value="non_veg">Non-Vegetarian</option>
                  <option value="vegan">Vegan</option>
                  <option value="halal">Halal</option>
                  <option value="jain">Jain (No Root Veg)</option>
                </select>
              </div>
            </div>

            {/* Quantities */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '5px' }}>
                  Total Quantity (kg)
                </label>
                <input
                  type="number"
                  step="0.5"
                  className="input-field tabular-numbers"
                  value={quantityKg}
                  onChange={(e) => setQuantityKg(parseFloat(e.target.value) || 0)}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '5px' }}>
                  Estimated Portions
                </label>
                <input
                  type="number"
                  className="input-field tabular-numbers"
                  value={portions}
                  onChange={(e) => setPortions(parseInt(e.target.value) || 0)}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Section 3: Pickup Location & Geolocation */}
        <div style={{ marginBottom: '24px' }}>
          <div className="inset-section-label">
            Pickup Location &amp; Spatial Dispatch Point
          </div>
          <div className="apple-card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <h4 style={{ fontSize: '13.5px', fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 2px 0' }}>
                  Pickup Address &amp; Place Name
                </h4>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0 }}>
                  Used to calculate transit ETAs for recipient NGOs and 2-Opt volunteer couriers.
                </p>
              </div>

              {/* Get My Location Button */}
              <button
                type="button"
                onClick={handleGetLocation}
                disabled={locating}
                className="btn btn-secondary"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 14px',
                  fontSize: '12.5px',
                  fontWeight: 600,
                  color: 'var(--accent-primary)',
                  borderColor: 'rgba(27, 122, 67, 0.3)',
                  background: locating ? 'rgba(27, 122, 67, 0.08)' : 'rgba(27, 122, 67, 0.05)',
                }}
              >
                {locating ? (
                  <>
                    <Loader2 size={14} className="spin" />
                    <span>Detecting Place...</span>
                  </>
                ) : (
                  <>
                    <Navigation size={14} />
                    <span>Get My Location</span>
                  </>
                )}
              </button>
            </div>

            {locationError && (
              <div
                style={{
                  background: 'rgba(215, 0, 21, 0.08)',
                  border: '1px solid rgba(215, 0, 21, 0.2)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '8px 12px',
                  color: 'var(--accent-red)',
                  marginBottom: '14px',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <AlertTriangle size={14} />
                <span>{locationError}</span>
              </div>
            )}

            {locationStatusText && (
              <div
                style={{
                  background: 'rgba(27, 122, 67, 0.08)',
                  border: '1px solid rgba(27, 122, 67, 0.2)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '8px 12px',
                  color: 'var(--accent-primary)',
                  marginBottom: '14px',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <CheckCircle2 size={14} />
                <span>{locationStatusText}</span>
              </div>
            )}

            {/* Editable Place Name Input */}
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '5px' }}>
                Place Name / Address *
              </label>
              <div style={{ position: 'relative' }}>
                <MapPin size={15} color="var(--accent-primary)" style={{ position: 'absolute', left: '12px', top: '11px' }} />
                <input
                  type="text"
                  required
                  className="input-field"
                  placeholder="e.g. Palace Grounds, MG Road, Bengaluru"
                  value={placeName}
                  onChange={(e) => setPlaceName(e.target.value)}
                  style={{ paddingLeft: '34px' }}
                />
              </div>
            </div>

            {/* Geocoordinates Badge & Manual Coordinates */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '12px',
                padding: '12px',
                background: 'rgba(0, 0, 0, 0.02)',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
                marginBottom: '14px',
              }}
            >
              <div>
                <label style={{ display: 'block', fontSize: '11.5px', color: 'var(--text-tertiary)', marginBottom: '3px' }}>
                  Latitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  className="input-field tabular-numbers"
                  value={latitude}
                  onChange={(e) => setLatitude(parseFloat(e.target.value) || 0)}
                  style={{ padding: '6px 10px', fontSize: '12.5px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '11.5px', color: 'var(--text-tertiary)', marginBottom: '3px' }}>
                  Longitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  className="input-field tabular-numbers"
                  value={longitude}
                  onChange={(e) => setLongitude(parseFloat(e.target.value) || 0)}
                  style={{ padding: '6px 10px', fontSize: '12.5px' }}
                />
              </div>
            </div>

            {/* Quick Preset Places */}
            <div>
              <div style={{ fontSize: '11.5px', color: 'var(--text-tertiary)', marginBottom: '6px' }}>
                Quick Preset Locations:
              </div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {Object.entries(PRESET_LOCATIONS).map(([key, preset]) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => handleApplyPreset(preset)}
                    className="btn btn-secondary"
                    style={{
                      padding: '4px 10px',
                      fontSize: '11.5px',
                      borderRadius: '6px',
                    }}
                  >
                    📍 {preset.placeName}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '16px' }}>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Publishing...' : 'Publish Surplus'}
          </button>
        </div>
      </form>
    </div>
  );
};
