import { useState, useEffect, useRef, RefObject } from 'react';

interface BracketFit {
  containerRef: RefObject<HTMLDivElement>;
  scale: number;
  width: number;
  height: number;
}

export function useBracketFit(
  designWidth: number,
  designHeight: number,
  maxViewportRatio = 0.68
): BracketFit {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const update = () => {
      const el = containerRef.current;
      if (!el) return;

      const availableWidth = el.clientWidth;
      const availableHeight = Math.min(
        window.innerHeight * maxViewportRatio,
        designHeight
      );

      const next = Math.min(
        availableWidth / designWidth,
        availableHeight / designHeight,
        1
      );

      setScale(next > 0 ? next : 1);
    };

    update();
    const observer = new ResizeObserver(update);
    if (containerRef.current) observer.observe(containerRef.current);
    window.addEventListener('resize', update);

    return () => {
      observer.disconnect();
      window.removeEventListener('resize', update);
    };
  }, [designWidth, designHeight, maxViewportRatio]);

  return {
    containerRef,
    scale,
    width: designWidth,
    height: designHeight,
  };
}
