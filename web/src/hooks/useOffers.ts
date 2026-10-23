import { useEffect, useState } from 'react';
import { api, MatchOffer } from '../lib/api';

export function useOffers(ngoId: string, pollIntervalMs = 4000) {
  const [offers, setOffers] = useState<MatchOffer[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchOffers = async () => {
    if (!ngoId) return;
    const data = await api.getOffersForNgo(ngoId);
    setOffers(data);
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
