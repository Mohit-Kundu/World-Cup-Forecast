import React from 'react';
import TeamRow from './TeamRow';
import { MatchResult, TeamStats } from '../../types';
import { getTeamStats } from '../../utils/safeData';

interface MatchCardProps {
  matchId: number;
  match: MatchResult | null;
  teamStats: Record<string, TeamStats>;
}

const MatchCard: React.FC<MatchCardProps> = ({ matchId, match, teamStats }) => {
  if (!match) {
    return (
      <div className="my-1 rounded-md border border-muted/20 bg-background px-2 py-1.5">
        <div className="text-[9px] text-muted">M{matchId}</div>
        <div className="text-[10px] text-muted">TBD</div>
      </div>
    );
  }

  const homeWinner = match.home_win_prob > match.away_win_prob;
  const awayWinner = match.away_win_prob > match.home_win_prob;

  return (
    <div className="my-1 rounded-md border border-muted/20 bg-background px-2 py-1.5 transition-colors hover:border-muted/40">
      <div className="mb-1 text-[9px] text-muted">M{matchId}</div>

      <TeamRow
        team={match.home_team}
        goals={match.most_common_home_goals}
        probability={match.home_win_prob}
        isWinner={homeWinner}
        stats={getTeamStats(teamStats, match.home_team)}
      />

      <TeamRow
        team={match.away_team}
        goals={match.most_common_away_goals}
        probability={match.away_win_prob}
        isWinner={awayWinner}
        stats={getTeamStats(teamStats, match.away_team)}
      />
    </div>
  );
};

export default MatchCard;
