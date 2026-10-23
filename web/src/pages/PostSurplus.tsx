import React, { useState } from 'react';
import { Sparkles, Upload, ArrowLeft, AlertTriangle } from 'lucide-react';
import { api } from '../lib/api';
import { UserSession } from '../firebase';

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

  // Gemini AI Analysis state
  const [analyzing, setAnalyzing] = useState(false);
  const [aiResult, setAiResult] = useState<any>(null);
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
    try {
      const res = await api.analyzePhoto(b64, title || 'Catering surplus');
      setAiResult(res);
      if (res.estimated_portions) {
        setPortions(res.estimated_portions);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title) {
      setErrorMsg('Please enter a descriptive food title.');
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
          latitude: 12.9716,
          longitude: 77.5946,
          address: 'Palace Grounds, MG Road, Bangalore',
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
    <div style={{ maxWidth: '740px', margin: '0 auto' }}>
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

          <div className="inset-group" style={{ padding: '20px', marginBottom: 0 }}>
            <div
              style={{
                border: '1px dashed var(--border-medium)',
                borderRadius: 'var(--radius-sm)',
                padding: '20px 16px',
                textAlign: 'center',
                background: 'var(--bg-app)',
                cursor: 'pointer',
                position: 'relative',
                transition: 'border-color 0.14s ease',
              }}
            >
              <input
                type="file"
                accept="image/*"
                onChange={handlePhotoUpload}
                style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }}
              />

              {photoBase64 ? (
                <div>
                  <img
                    src={photoBase64}
                    alt="Uploaded food"
                    style={{ maxHeight: '140px', borderRadius: '8px', margin: '0 auto 8px', display: 'block' }}
                  />
                  <span style={{ fontSize: '12px', color: 'var(--accent-primary)', fontWeight: 500 }}>
                    Photo attached &bull; Click to replace
                  </span>
                </div>
              ) : (
                <div>
                  <Upload size={20} color="var(--text-tertiary)" style={{ margin: '0 auto 6px' }} />
                  <p style={{ color: 'var(--text-primary)', fontSize: '13px', fontWeight: 500, marginBottom: '2px' }}>
                    Click or drop surplus food photo
                  </p>
                  <p style={{ color: 'var(--text-tertiary)', fontSize: '11.5px', margin: 0 }}>
                    Multimodal inspection analyzes portion count, safety packaging, and freshness
                  </p>
                </div>
              )}
            </div>

            {analyzing && (
              <div style={{ marginTop: '12px', color: 'var(--text-secondary)', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'var(--accent-primary)' }} />
                <span>Inspecting food safety standards and estimated portions...</span>
              </div>
            )}

            {aiResult && !analyzing && (
              <div
                style={{
                  marginTop: '12px',
                  background: 'rgba(0, 0, 0, 0.025)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '10px 14px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '12.5px' }}>
                    Inspection Analysis ({(aiResult.confidence * 100).toFixed(0)}% Confidence)
                  </span>
                  <span className="badge badge-green" style={{ fontSize: '10.5px' }}>Verified</span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '3px' }}>
                  Type: <strong style={{ color: 'var(--text-primary)' }}>{aiResult.food_type}</strong> &bull; Estimated Portions: <strong style={{ color: 'var(--text-primary)' }}>{aiResult.estimated_portions}</strong> &bull; Shelf Life: <strong style={{ color: 'var(--text-primary)' }}>{aiResult.shelf_life_hours_hint} hrs</strong>
                </div>
                {aiResult.safety_flags && (
                  <div style={{ fontSize: '11.5px', color: 'var(--text-tertiary)' }}>
                    Flags: {aiResult.safety_flags.join(', ')}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Section 2: Food Information */}
        <div style={{ marginBottom: '22px' }}>
          <div className="inset-section-label">
            Surplus Information
          </div>

          <div className="inset-group" style={{ padding: '18px 20px', marginBottom: 0 }}>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '5px' }}>
                Surplus Title *
              </label>
              <input
                type="text"
                className="input-field"
                placeholder="e.g. 50 Portions Veg Biryani & Dal Makhani"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '5px' }}>
                Preparation Details &amp; Packaging Notes
              </label>
              <textarea
                className="input-field"
                rows={3}
                placeholder="Freshly prepared banquet food, sealed in food-grade thermal containers."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Section 3: Safe Storage & Classification */}
        <div style={{ marginBottom: '22px' }}>
          <div className="inset-section-label">
            Storage &amp; Classification
          </div>

          <div className="inset-group" style={{ padding: '18px 20px', marginBottom: 0 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '5px' }}>
                  Food Category
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
