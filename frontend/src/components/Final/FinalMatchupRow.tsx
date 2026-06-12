import React from 'react';

interface FinalMatchupRowProps {
  left?: React.ReactNode;
  center: React.ReactNode;
  right?: React.ReactNode;
  className?: string;
}

/** Shared 3-column row: w-11 gutters + flex-1 center (matches outcome bar layout). */
const FinalMatchupRow: React.FC<FinalMatchupRowProps> = ({
  left,
  center,
  right,
  className = '',
}) => (
  <div className={`flex items-center gap-3 ${className}`}>
    <div className="w-11 shrink-0 text-right text-xs tabular-nums">{left}</div>
    <div className="min-w-0 flex-1">{center}</div>
    <div className="w-11 shrink-0 text-left text-xs tabular-nums">{right}</div>
  </div>
);

export default FinalMatchupRow;
