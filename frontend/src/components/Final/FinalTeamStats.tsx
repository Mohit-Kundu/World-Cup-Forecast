import React from 'react';
import { TeamStats } from '../../types';
import { getTeamStats } from '../../utils/safeData';
import { TEAM_STAT_TOOLTIPS, TeamStatKey } from '../../utils/teamStatTooltips';
import HelpTooltip from '../HelpTooltip';
import { finalAccentTextStyle } from './finalColors';
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

const STAT_ROWS: { key: keyof TeamOverview; statKey: TeamStatKey }[] = [
  { key: 'qualify', statKey: 'qualify' },
  { key: 'champ', statKey: 'champ' },
  { key: 'elo', statKey: 'elo' },
  { key: 'form', statKey: 'form' },
  { key: 'attack', statKey: 'attack' },
  { key: 'defense', statKey: 'defense' },
];

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

  return (
    <div className="space-y-1 border-t border-muted/20 px-3 pt-4 sm:px-4">
      {STAT_ROWS.map(({ key, statKey }) => {
        const { label, tooltip } = TEAM_STAT_TOOLTIPS[statKey];
        return (
          <FinalMatchupRow
            key={key}
            left={
              <span className="font-medium" style={finalAccentTextStyle(leftIsWinner)}>
                {leftOverview[key]}
              </span>
            }
            center={
              <div className="flex justify-center">
                <span className="inline-flex items-center gap-0.5 text-[11px] leading-5 text-muted">
                  {label}
                  <HelpTooltip text={tooltip} />
                </span>
              </div>
            }
            right={
              <span className="font-medium" style={finalAccentTextStyle(rightIsWinner)}>
                {rightOverview[key]}
              </span>
            }
          />
        );
      })}
    </div>
  );
};

export default FinalTeamStats;
