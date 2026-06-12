import React, { useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import FlagImage from './FlagImage';
import { useFloatingTooltipPosition } from '../hooks/useFloatingTooltipPosition';
import { TeamStats } from '../types';

const TOOLTIP_WIDTH = 224;

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
  const anchorRef = useRef<HTMLDivElement>(null);
  const position = useFloatingTooltipPosition(anchorRef, showTooltip, {
    placement: 'top',
    width: TOOLTIP_WIDTH,
  });

  return (
    <div
      ref={anchorRef}
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <FlagImage team={team} className={flagClassName} />

      {showTooltip &&
        position &&
        createPortal(
          <div
            className="fixed z-[9999] w-56 rounded-md border border-muted/30 bg-surface p-3 shadow-xl"
            style={{
              top: position.top,
              left: position.left,
              transform: position.transform,
            }}
          >
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
          </div>,
          document.body
        )}
    </div>
  );
};

export default FlagTooltip;
