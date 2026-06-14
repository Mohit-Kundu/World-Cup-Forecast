import React, { useEffect, useMemo, useRef } from 'react';
import { useIsMonitorLayout } from '../../hooks/useIsMonitorLayout';
import { PredictionsData } from '../../types';
import { resolveAwardCards } from '../../utils/wrappedAwards';
import AwardCard from './AwardCard';

interface WorldCupWrappedProps {
  data?: PredictionsData;
  showHeading?: boolean;
}

const CARDS_PER_VIEW = 4;
const SCROLL_GAP_REM = 0.875;
const SCROLL_GAPS_TOTAL = `${(CARDS_PER_VIEW - 1) * SCROLL_GAP_REM}rem`;

const WorldCupWrapped: React.FC<WorldCupWrappedProps> = ({ data, showHeading = true }) => {
  const isMonitor = useIsMonitorLayout();
  const cards = useMemo(() => resolveAwardCards(data), [data]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container) return;

    const onWheel = (event: WheelEvent) => {
      const maxScrollLeft = container.scrollWidth - container.clientWidth;
      if (maxScrollLeft <= 0) return;

      const { deltaX, deltaY } = event;
      const dominantDelta =
        Math.abs(deltaX) > Math.abs(deltaY) ? deltaX : deltaY;
      if (dominantDelta === 0) return;

      const atStart = container.scrollLeft <= 0;
      const atEnd = container.scrollLeft >= maxScrollLeft - 1;
      const canScroll =
        (dominantDelta > 0 && !atEnd) || (dominantDelta < 0 && !atStart);

      if (!canScroll) return;

      event.preventDefault();
      event.stopPropagation();
      container.scrollLeft += dominantDelta;
    };

    container.addEventListener('wheel', onWheel, { passive: false });
    return () => container.removeEventListener('wheel', onWheel);
  }, [cards.length]);

  return (
    <section>
      {showHeading && (
        <div className="mb-4">
          <h2 className="text-sm font-medium text-primary">World Cup Wrapped</h2>
          <p className="mt-1 text-xs text-muted">
            Standout teams and groups from across all simulations.
          </p>
        </div>
      )}

      <div
        ref={scrollRef}
        className="award-cards-scroll flex w-full flex-nowrap gap-3.5 overflow-x-auto pb-3 pt-2 scrollbar-hide"
        style={{
          height: isMonitor ? '260px' : '350px',
        }}
      >
        {cards.map((card) => (
          <div
            key={card.id}
            className="h-full shrink-0"
            style={{
              flex: `0 0 calc((100% - ${SCROLL_GAPS_TOTAL}) / ${CARDS_PER_VIEW})`,
            }}
          >
            <AwardCard
              card={card}
              variant={isMonitor ? 'default' : 'laptop'}
              className="h-full w-full"
            />
          </div>
        ))}
      </div>
    </section>
  );
};

export default WorldCupWrapped;
