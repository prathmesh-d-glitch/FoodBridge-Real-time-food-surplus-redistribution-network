import { useEffect, useState } from 'react';
import { api, DonorListing } from '../lib/api';

export function useListings(statusFilter?: string, pollIntervalMs = 5000) {
  const [listings, setListings] = useState<DonorListing[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchListings = async () => {
    const data = await api.getListings(statusFilter);
    setListings(data);
    setLoading(false);
  };

  useEffect(() => {
    fetchListings();
    const interval = setInterval(fetchListings, pollIntervalMs);
    return () => clearInterval(interval);
  }, [statusFilter, pollIntervalMs]);

  return {
    listings,
    loading,
    refresh: fetchListings,
  };
}
