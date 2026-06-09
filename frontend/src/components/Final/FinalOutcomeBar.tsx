import React from 'react';
import FlagImage from '../FlagImage';

const WINNER_COLOR = '#BFA046';
const RUNNER_COLOR = '#C8CDD3';

interface FinalOutcomeBarProps {
  leftTeam: string;
  rightTeam: string;
  leftProb: number;
  rightProb: number;
  leftIsWinner: boolean;
  rightIsWinner: boolean;
}

const FinalOutcomeBar: React.FC<FinalOutcomeBarProps> = ({
  leftTeam,
  rightTeam,
  leftProb,
  rightProb,
  leftIsWinner,
  rightIsWinner,
}) => {
  const leftPct = (leftProb * 100).toFixed(1);
  const rightPct = (rightProb * 100).toFixed(1);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-4">
        <div className="flex min-w-0 items-center gap-2">
          <FlagImage team={leftTeam} className="h-5 w-7 shrink-0 rounded-sm object-cover ring-1 ring-muted/40" />
          <span
            className="truncate text-sm font-medium"
            style={{ color: leftIsWinner ? WINNER_COLOR : RUNNER_COLOR }}
          >
            {leftTeam}
          </span>
        </div>
        <span className="shrink-0 text-[10px] font-medium uppercase tracking-widest text-muted">vs</span>
        <div className="flex min-w-0 items-center justify-end gap-2">
          <span
            className="truncate text-sm font-medium"
            style={{ color: rightIsWinner ? WINNER_COLOR : RUNNER_COLOR }}
          >
            {rightTeam}
          </span>
          <FlagImage team={rightTeam} className="h-5 w-7 shrink-0 rounded-sm object-cover ring-1 ring-muted/40" />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <span
          className="w-11 shrink-0 text-right text-xs tabular-nums"
          style={{ color: leftIsWinner ? WINNER_COLOR : RUNNER_COLOR, fontWeight: leftIsWinner ? 500 : 400 }}
        >
          {leftPct}%
        </span>

        <div className="flex h-5 flex-1 overflow-hidden rounded-md">
          <div
            className="h-full transition-all"
            style={{
              width: `${leftProb * 100}%`,
              backgroundColor: leftIsWinner ? WINNER_COLOR : RUNNER_COLOR,
            }}
          />
          <div
            className="h-full transition-all"
            style={{
              width: `${rightProb * 100}%`,
              backgroundColor: rightIsWinner ? WINNER_COLOR : RUNNER_COLOR,
            }}
          />
        </div>

        <span
          className="w-11 shrink-0 text-left text-xs tabular-nums"
          style={{ color: rightIsWinner ? WINNER_COLOR : RUNNER_COLOR, fontWeight: rightIsWinner ? 500 : 400 }}
        >
          {rightPct}%
        </span>
      </div>
    </div>
  );
};

export default FinalOutcomeBar;
