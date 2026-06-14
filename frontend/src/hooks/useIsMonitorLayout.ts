import { useEffect, useState } from 'react';

export function useIsMonitorLayout() {
  const [isMonitor, setIsMonitor] = useState(
    () => window.matchMedia('(min-width: 1536px)').matches
  );

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 1536px)');
    const onChange = (event: MediaQueryListEvent) => setIsMonitor(event.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  return isMonitor;
}
