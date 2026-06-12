import { RefObject, useLayoutEffect, useState } from 'react';

const VIEWPORT_PADDING = 8;
const GAP = 6;

export interface FloatingPosition {
  top: number;
  left: number;
  transform: string;
}

interface UseFloatingTooltipPositionOptions {
  placement: 'top' | 'bottom';
  align?: 'center' | 'right';
  width: number;
}

export function useFloatingTooltipPosition(
  anchorRef: RefObject<HTMLElement | null>,
  visible: boolean,
  { placement, align = 'center', width }: UseFloatingTooltipPositionOptions
): FloatingPosition | null {
  const [position, setPosition] = useState<FloatingPosition | null>(null);

  useLayoutEffect(() => {
    if (!visible || !anchorRef.current) {
      setPosition(null);
      return;
    }

    const updatePosition = () => {
      const anchor = anchorRef.current;
      if (!anchor) return;

      const rect = anchor.getBoundingClientRect();
      const top = placement === 'top' ? rect.top - GAP : rect.bottom + GAP;
      const transform =
        placement === 'top'
          ? align === 'right'
            ? 'translate(-100%, -100%)'
            : 'translate(-50%, -100%)'
          : align === 'right'
            ? 'translate(-100%, 0)'
            : 'translate(-50%, 0)';

      let left: number;
      if (align === 'right') {
        const rawLeft = rect.right - width;
        const clampedLeft = Math.max(
          VIEWPORT_PADDING,
          Math.min(rawLeft, window.innerWidth - width - VIEWPORT_PADDING)
        );
        left = clampedLeft + width;
      } else {
        const center = rect.left + rect.width / 2;
        const clampedCenter = Math.max(
          VIEWPORT_PADDING + width / 2,
          Math.min(center, window.innerWidth - VIEWPORT_PADDING - width / 2)
        );
        left = clampedCenter;
      }

      setPosition({ top, left, transform });
    };

    updatePosition();
    window.addEventListener('scroll', updatePosition, true);
    window.addEventListener('resize', updatePosition);

    return () => {
      window.removeEventListener('scroll', updatePosition, true);
      window.removeEventListener('resize', updatePosition);
    };
  }, [visible, anchorRef, placement, align, width]);

  return position;
}
