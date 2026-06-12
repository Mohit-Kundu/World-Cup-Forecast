import React, { useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useFloatingTooltipPosition } from '../hooks/useFloatingTooltipPosition';

const TOOLTIP_WIDTH = 208;

interface HelpTooltipProps {
  text: string;
  alignRight?: boolean;
}

const HelpTooltip: React.FC<HelpTooltipProps> = ({ text, alignRight = false }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const anchorRef = useRef<HTMLSpanElement>(null);
  const position = useFloatingTooltipPosition(anchorRef, showTooltip, {
    placement: 'bottom',
    align: alignRight ? 'right' : 'center',
    width: TOOLTIP_WIDTH,
  });

  return (
    <span
      ref={anchorRef}
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

      {showTooltip &&
        position &&
        createPortal(
          <div
            className="fixed z-[9999] w-52 rounded-md border border-muted/30 bg-surface p-2.5 shadow-xl"
            style={{
              top: position.top,
              left: position.left,
              transform: position.transform,
            }}
          >
            <p className="text-[11px] font-normal normal-case leading-snug tracking-normal text-primary">
              {text}
            </p>
          </div>,
          document.body
        )}
    </span>
  );
};

export default HelpTooltip;
