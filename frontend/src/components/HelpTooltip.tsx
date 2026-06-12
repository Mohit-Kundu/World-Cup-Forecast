import React, { useState } from 'react';

interface HelpTooltipProps {
  text: string;
  alignRight?: boolean;
}

const HelpTooltip: React.FC<HelpTooltipProps> = ({ text, alignRight = false }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <span
      className="relative inline-flex shrink-0"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      onClick={(e) => e.stopPropagation()}
    >
      <span
        className="inline-flex h-3.5 w-3.5 cursor-help items-center justify-center rounded-full border border-muted/40 text-[8px] font-medium normal-case tracking-normal text-muted/70 transition-colors hover:border-muted/60 hover:text-primary"
        aria-label="Column help"
      >
        ?
      </span>

      {showTooltip && (
        <div
          className={`absolute top-[125%] z-50 w-52 rounded-md border border-muted/30 bg-surface p-2.5 shadow-xl ${
            alignRight ? 'right-0' : 'left-1/2 -translate-x-1/2'
          }`}
        >
          <p className="text-[11px] font-normal normal-case leading-snug tracking-normal text-primary">
            {text}
          </p>
        </div>
      )}
    </span>
  );
};

export default HelpTooltip;
