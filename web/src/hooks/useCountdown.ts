import { useEffect, useState } from 'react';

export function useCountdown(targetIsoDate: string) {
  const calculateSecondsLeft = () => {
    const diff = new Date(targetIsoDate).getTime() - Date.now();
    return Math.max(0, Math.floor(diff / 1000));
  };

  const [secondsLeft, setSecondsLeft] = useState(calculateSecondsLeft);

  useEffect(() => {
    setSecondsLeft(calculateSecondsLeft());
    const interval = setInterval(() => {
      const left = calculateSecondsLeft();
      setSecondsLeft(left);
      if (left <= 0) {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [targetIsoDate]);

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  const isExpired = secondsLeft <= 0;

  return {
    secondsLeft,
    minutes,
    seconds,
    formatted: `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`,
    isExpired,
  };
}
