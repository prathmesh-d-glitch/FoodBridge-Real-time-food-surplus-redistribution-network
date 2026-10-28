export function getRemainingMinutes(safeUntilIso: string): number {
  const deadline = new Date(safeUntilIso).getTime();
  const now = Date.now();
  const diffMs = deadline - now;
  return Math.max(0, Math.round(diffMs / (1000 * 60)));
}

export function formatRemainingTime(minutes: number): string {
  if (minutes <= 0) return 'Expired';
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours > 0) {
    return `${hours}h ${mins}m left`;
  }
  return `${mins}m left`;
}

export type FreshnessState = 'fresh' | 'warning' | 'urgent' | 'expired';

export function getFreshnessState(remainingMinutes: number): FreshnessState {
  if (remainingMinutes <= 0) return 'expired';
  if (remainingMinutes <= 45) return 'urgent';
  if (remainingMinutes <= 90) return 'warning';
  return 'fresh';
}
