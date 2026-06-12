import React from 'react';

interface SnapPageIndicatorProps {
  current: number;
  total: number;
}

const SnapPageIndicator: React.FC<SnapPageIndicatorProps> = ({ current, total }) => (
  <div
    className="text-sm tabular-nums leading-5"
    aria-live="polite"
    aria-label={`Page ${current} of ${total}`}
  >
    <span className="font-medium text-gold">{current}</span>
    <span className="text-muted"> / {total}</span>
  </div>
);

export default SnapPageIndicator;
