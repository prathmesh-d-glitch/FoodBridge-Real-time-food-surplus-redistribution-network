import { useEffect, useState } from 'react';
import { api, MatchOffer } from '../lib/api';

export function useOffers(ngoId: string, pollIntervalMs = 4000) {
  const [offers, setOffers] = useState<MatchOffer[]>([]);
  const [loading, setLoading] = useState(true);

  const getSavedStatusOverrides = (): Record<string, string> => {
    try {
      const saved = localStorage.getItem('foodbridge_offer_status_overrides');
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  };

  const fetchOffers = async () => {
    if (!ngoId) return;
    const data = await api.getOffersForNgo(ngoId);
    const overrides = getSavedStatusOverrides();

    const merged = data.map((o) => {
      if (overrides[o.id]) {
        return { ...o, status: overrides[o.id] as any };
      }
      return o;
    });

    setOffers(merged);
    setLoading(false);
  };

  useEffect(() => {
    fetchOffers();
    const interval = setInterval(fetchOffers, pollIntervalMs);
    return () => clearInterval(interval);
  }, [ngoId, pollIntervalMs]);

  return {
    offers,
    loading,
    refresh: fetchOffers,
  };
}
