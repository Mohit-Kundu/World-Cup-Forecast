import React from 'react';
import MatchCard from './MatchCard';
import { MatchResult, TeamStats } from '../../types';

interface BracketColumnProps {
  title: string;
  matchIds: number[];
  matchResults: Record<string, MatchResult>;
  teamStats: Record<string, TeamStats>;
}

const BracketColumn: React.FC<BracketColumnProps> = ({ title, matchIds, matchResults, teamStats }) => {
  return (
    <div className="mx-0.5 flex h-full min-w-[158px] flex-1 flex-col justify-around">
      <div className="mb-2 text-center text-[10px] font-medium uppercase tracking-widest text-muted">
        {title}
      </div>
      <div className="flex h-full flex-col justify-around">
        {matchIds.map((id) => (
          <MatchCard
            key={id}
            matchId={id}
            match={matchResults[String(id)] ?? null}
            teamStats={teamStats}
          />
        ))}
      </div>
    </div>
  );
};

export default BracketColumn;
