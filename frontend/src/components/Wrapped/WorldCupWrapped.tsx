import React, { useMemo } from 'react';
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
        className="grid w-full grid-flow-col gap-3.5 overflow-x-auto pb-3 scrollbar-hide"
        style={{
          height: isMonitor ? '260px' : '350px',
          gridAutoColumns: `calc((100% - ${SCROLL_GAPS_TOTAL}) / ${CARDS_PER_VIEW})`,
        }}
      >
        {cards.map((card) => (
          <AwardCard
            key={card.id}
            card={card}
            variant={isMonitor ? 'default' : 'laptop'}
            className="h-full w-full min-w-0"
          />
        ))}
      </div>
    </section>
  );
};

export default WorldCupWrapped;
