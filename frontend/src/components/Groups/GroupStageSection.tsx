import React, { useState } from 'react';
import GroupTable from './GroupTable';
import { PredictionsData } from '../../types';

interface GroupStageSectionProps {
  data: PredictionsData;
}

const GROUP_ORDER = 'ABCDEFGHIJKL'.split('');
const GROUPS_PER_PAGE = 6;

const btnClass =
  'inline-flex h-8 items-center justify-center rounded-md border border-muted/40 px-2 text-xs text-primary transition-colors hover:border-muted/60 disabled:cursor-not-allowed disabled:opacity-40';

const GroupStageSection: React.FC<GroupStageSectionProps> = ({ data }) => {
  const groupStandings = data.group_standings ?? {};
  const [page, setPage] = useState(1);

  const totalPages = Math.max(1, Math.ceil(GROUP_ORDER.length / GROUPS_PER_PAGE));
  const safePage = Math.min(page, totalPages);
  const pageStart = (safePage - 1) * GROUPS_PER_PAGE;
  const pageGroups = GROUP_ORDER.slice(pageStart, pageStart + GROUPS_PER_PAGE);
  const rangeStart = pageStart + 1;
  const rangeEnd = Math.min(pageStart + GROUPS_PER_PAGE, GROUP_ORDER.length);

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

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
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
