import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import GroupTable from './GroupTable';
import { useIsMonitorLayout } from '../../hooks/useIsMonitorLayout';
import { PredictionsData } from '../../types';

interface GroupStageSectionProps {
  data: PredictionsData;
}

const GROUP_ORDER = 'ABCDEFGHIJKL'.split('');

function useGridColumnCount(gridRef: React.RefObject<HTMLDivElement | null>) {
  const [columnCount, setColumnCount] = useState(() =>
    window.matchMedia('(min-width: 640px)').matches ? 3 : 1
  );

  useLayoutEffect(() => {
    const grid = gridRef.current;
    if (!grid) return;

    const readColumns = () => {
      const template = window.getComputedStyle(grid).gridTemplateColumns;
      const count = template
        .split(' ')
        .filter((part) => part && part !== '/')
        .length;
      setColumnCount(Math.max(1, count));
    };

    readColumns();
    const observer = new ResizeObserver(readColumns);
    observer.observe(grid);
    window.addEventListener('resize', readColumns);
    return () => {
      observer.disconnect();
      window.removeEventListener('resize', readColumns);
    };
  }, []);

  return columnCount;
}

const btnClass =
  'inline-flex h-8 items-center justify-center rounded-md border border-muted/40 px-2 text-xs text-primary transition-colors hover:border-muted/60 disabled:cursor-not-allowed disabled:opacity-40';

const GroupStageSection: React.FC<GroupStageSectionProps> = ({ data }) => {
  const groupStandings = data.group_standings ?? {};
  const gridRef = useRef<HTMLDivElement>(null);
  const columnCount = useGridColumnCount(gridRef);
  const isMonitor = useIsMonitorLayout();
  const groupsPerPage = isMonitor ? columnCount * 2 : columnCount;
  const [page, setPage] = useState(1);

  useEffect(() => {
    setPage(1);
  }, [groupsPerPage]);

  const totalPages = Math.max(1, Math.ceil(GROUP_ORDER.length / groupsPerPage));
  const safePage = Math.min(page, totalPages);
  const pageStart = (safePage - 1) * groupsPerPage;
  const pageGroups = GROUP_ORDER.slice(pageStart, pageStart + groupsPerPage);
  const rangeStart = pageStart + 1;
  const rangeEnd = Math.min(pageStart + groupsPerPage, GROUP_ORDER.length);

  return (
    <section>
      <div className="mb-4 space-y-3">
        <div>
          <h2 className="text-sm font-medium text-primary">Group Stage</h2>
          <p className="mt-1 text-xs text-muted">
            Predicted standings from most common scorelines. Qual% = probability of finishing top 2.
          </p>
          <p className="mt-1 text-[10px] text-muted/70">
            Showing groups {rangeStart}–{rangeEnd} of {GROUP_ORDER.length}
          </p>
        </div>

        <div className="flex flex-nowrap items-center justify-end gap-1.5">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={safePage <= 1}
            className={btnClass}
            aria-label="Previous page"
          >
            ‹
          </button>
          <span className="inline-flex h-8 min-w-[3.5rem] items-center justify-center text-xs tabular-nums text-primary">
            {safePage} / {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={safePage >= totalPages}
            className={btnClass}
            aria-label="Next page"
          >
            ›
          </button>
        </div>
      </div>

      <div ref={gridRef} className="group-stage-grid grid grid-cols-1 gap-3 sm:grid-cols-3">
        {pageGroups.map((group) => (
          <GroupTable
            key={group}
            group={group}
            standings={groupStandings[group] ?? []}
            teamStats={data.team_stats ?? {}}
          />
        ))}
      </div>
    </section>
  );
};

export default GroupStageSection;
