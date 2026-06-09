import React from 'react';
import FlagTooltip from '../FlagTooltip';
import { TeamStats } from '../../types';

interface TeamRowProps {
  team: string;
  goals: number;
  probability: number;
  isWinner: boolean;
  stats: TeamStats;
}

const TeamRow: React.FC<TeamRowProps> = ({ team, goals, probability, isWinner, stats }) => {
  return (
    <div
      className={`flex items-center justify-between rounded px-1 py-1 ${
        isWinner ? 'border-l-2 border-gold bg-surface' : ''
      }`}
    >
      <div className="flex min-w-0 items-center gap-2">
        <FlagTooltip team={team} stats={stats} />
        <span className={`truncate text-[10px] ${isWinner ? 'text-primary' : 'text-primary/90'}`} title={team}>
          {team}
        </span>
      </div>

      <div className="ml-2 flex shrink-0 items-center gap-2 tabular-nums">
        <span className="text-xs font-medium text-gold">{goals}</span>
        <span className={`text-[10px] ${isWinner ? 'text-gold' : 'text-muted'}`}>
          {(probability * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  );
};

export default TeamRow;
