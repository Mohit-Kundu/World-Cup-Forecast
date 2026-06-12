import React from 'react';
import FlagImage from '../FlagImage';
import {
  FINAL_RUNNER_BAR_COLOR,
  FINAL_RUNNER_COLOR,
  FINAL_WINNER_BAR_COLOR,
  FINAL_WINNER_COLOR,
} from './finalColors';
import FinalMatchupRow from './FinalMatchupRow';

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
  const leftTextColor = leftIsWinner ? FINAL_WINNER_COLOR : FINAL_RUNNER_COLOR;
  const rightTextColor = rightIsWinner ? FINAL_WINNER_COLOR : FINAL_RUNNER_COLOR;
  const leftBarColor = leftIsWinner ? FINAL_WINNER_BAR_COLOR : FINAL_RUNNER_BAR_COLOR;
  const rightBarColor = rightIsWinner ? FINAL_WINNER_BAR_COLOR : FINAL_RUNNER_BAR_COLOR;

  return (
    <div className="space-y-3">
      <FinalMatchupRow
        center={
          <div className="flex items-center justify-between gap-4">
            <div className="flex min-w-0 items-center gap-2">
              <FlagImage
                team={leftTeam}
                className="h-5 w-7 shrink-0 rounded-sm object-cover ring-1 ring-muted/40"
              />
              <span
                className="truncate text-sm font-medium"
                style={{ color: leftTextColor, fontWeight: leftIsWinner ? 600 : 500 }}
              >
                {leftTeam}
              </span>
            </div>
            <span className="shrink-0 text-[10px] font-medium uppercase tracking-widest text-muted">
              vs
            </span>
            <div className="flex min-w-0 items-center justify-end gap-2">
              <span
                className="truncate text-sm font-medium"
                style={{ color: rightTextColor, fontWeight: rightIsWinner ? 600 : 500 }}
              >
                {rightTeam}
              </span>
              <FlagImage
                team={rightTeam}
                className="h-5 w-7 shrink-0 rounded-sm object-cover ring-1 ring-muted/40"
              />
            </div>
          </div>
        }
      />

      <FinalMatchupRow
        left={
          <span style={{ color: leftTextColor, fontWeight: leftIsWinner ? 600 : 500 }}>
            {leftPct}%
          </span>
        }
        right={
          <span style={{ color: rightTextColor, fontWeight: rightIsWinner ? 600 : 500 }}>
            {rightPct}%
          </span>
        }
        center={
          <div className="flex h-5 overflow-hidden rounded-md">
            <div
              className="h-full transition-all"
              style={{ width: `${leftProb * 100}%`, backgroundColor: leftBarColor }}
            />
            <div
              className="h-full transition-all"
              style={{ width: `${rightProb * 100}%`, backgroundColor: rightBarColor }}
            />
          </div>
        }
      />
    </div>
  );
};

export default FinalOutcomeBar;
