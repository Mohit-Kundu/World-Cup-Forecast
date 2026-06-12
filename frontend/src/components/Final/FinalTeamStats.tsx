import React from 'react';
import { TeamStats } from '../../types';
import { getTeamStats } from '../../utils/safeData';
import { FINAL_RUNNER_COLOR, FINAL_WINNER_COLOR } from './finalColors';
import FinalMatchupRow from './FinalMatchupRow';

interface FinalTeamStatsProps {
  leftTeam: string;
  rightTeam: string;
  leftIsWinner: boolean;
  rightIsWinner: boolean;
  teamStats: Record<string, TeamStats>;
  qualifyProbs: Record<string, number>;
  championProbs: Record<string, number>;
}

interface TeamOverview {
  qualify: string;
  champ: string;
  elo: number;
  form: string;
  attack: string;
  defense: string;
}

function buildOverview(
  team: string,
  teamStats: Record<string, TeamStats>,
  qualifyProbs: Record<string, number>,
  championProbs: Record<string, number>
): TeamOverview {
  const stats = getTeamStats(teamStats, team);
  return {
    qualify: `${((qualifyProbs[team] ?? 0) * 100).toFixed(2)}%`,
    champ: `${((championProbs[team] ?? 0) * 100).toFixed(2)}%`,
    elo: parseInt(stats['FIFA ELO Rating'] ?? '1500', 10) || 1500,
    form: stats['Recent Form (W5)'] ?? '—',
    attack: (parseFloat(stats['Attack Strength (Avg Goals)'] ?? '0') || 0).toFixed(2),
    defense: (parseFloat(stats['Defense Rating (Inverse)'] ?? '0') || 0).toFixed(2),
  };
}

const STAT_ROWS: { key: keyof TeamOverview; label: string }[] = [
  { key: 'qualify', label: 'Qualify' },
  { key: 'champ', label: 'Champ' },
  { key: 'elo', label: 'Elo' },
  { key: 'form', label: 'Form' },
  { key: 'attack', label: 'Atk' },
  { key: 'defense', label: 'Def' },
];

const LABEL_WIDTH = 'w-14';

const FinalTeamStats: React.FC<FinalTeamStatsProps> = ({
  leftTeam,
  rightTeam,
  leftIsWinner,
  rightIsWinner,
  teamStats,
  qualifyProbs,
  championProbs,
}) => {
  const leftOverview = buildOverview(leftTeam, teamStats, qualifyProbs, championProbs);
  const rightOverview = buildOverview(rightTeam, teamStats, qualifyProbs, championProbs);
  const leftColor = leftIsWinner ? FINAL_WINNER_COLOR : FINAL_RUNNER_COLOR;
  const rightColor = rightIsWinner ? FINAL_WINNER_COLOR : FINAL_RUNNER_COLOR;

  return (
    <div className="space-y-1 border-t border-muted/20 pt-4">
      {STAT_ROWS.map(({ key, label }) => (
        <FinalMatchupRow
          key={key}
          center={
            <div className="flex items-center text-[11px] leading-5">
              <span
                className="flex-1 text-right tabular-nums font-medium"
                style={{ color: leftColor }}
              >
                {leftOverview[key]}
              </span>
              <span className={`${LABEL_WIDTH} shrink-0 text-center text-muted`}>{label}</span>
              <span
                className="flex-1 text-left tabular-nums font-medium"
                style={{ color: rightColor }}
              >
                {rightOverview[key]}
              </span>
            </div>
          }
        />
      ))}
    </div>
  );
};

export default FinalTeamStats;
