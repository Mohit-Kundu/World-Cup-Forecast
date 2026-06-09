import React from 'react';
import FlagTooltip from '../FlagTooltip';
import { TeamStats } from '../../types';

interface ChampionBoxProps {
  champion: string;
  probability: number;
  stats: TeamStats;
}

const ChampionBox: React.FC<ChampionBoxProps> = ({ champion, probability, stats }) => {
  return (
    <div className="mt-4 rounded-md border border-gold/30 bg-surface px-3 py-3 text-center">
      <div className="mb-2 text-[10px] font-medium uppercase tracking-widest text-muted">
        Champion
      </div>

      <div className="flex items-center justify-center gap-2">
        <FlagTooltip team={champion} stats={stats} />
        <span className="text-sm font-medium text-primary">{champion}</span>
      </div>

      <div className="mt-2 text-xs tabular-nums text-gold">
        {(probability * 100).toFixed(1)}%
      </div>
    </div>
  );
};

export default ChampionBox;
