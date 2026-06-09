import React, { useState } from 'react';
import FlagImage from './FlagImage';
import { TeamStats } from '../types';

interface FlagTooltipProps {
  team: string;
  stats: TeamStats;
  flagClassName?: string;
}

const FlagTooltip: React.FC<FlagTooltipProps> = ({
  team,
  stats,
  flagClassName = 'h-3.5 w-5 cursor-pointer rounded-sm object-cover ring-1 ring-muted/40',
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <FlagImage team={team} className={flagClassName} />

      {showTooltip && (
        <div className="absolute bottom-[125%] left-1/2 z-50 w-56 -translate-x-1/2 rounded-md border border-muted/30 bg-surface p-3 shadow-xl">
          <p className="mb-2 flex items-center gap-2 border-b border-muted/20 pb-2 text-xs font-medium text-primary">
            <FlagImage team={team} />
            {team}
          </p>

          <div className="space-y-1.5">
            {Object.entries(stats).map(([key, value]) => (
              <div key={key} className="flex justify-between gap-3 text-[11px]">
                <span className="text-muted">{key}</span>
                <span className="text-right text-primary">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FlagTooltip;
