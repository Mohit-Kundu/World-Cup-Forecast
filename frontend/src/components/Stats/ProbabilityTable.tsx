import React, { useState, useMemo } from 'react';
import { TableDataItem, TeamStats } from '../../types';
import { getTeamStats } from '../../utils/safeData';
import FlagTooltip from '../FlagTooltip';

interface ProbabilityTableProps {
  data: TableDataItem[];
  teamStats: Record<string, TeamStats>;
}

type SortKey = keyof TableDataItem;
type SortOrder = 'asc' | 'desc';

const ProbabilityTable: React.FC<ProbabilityTableProps> = ({ data, teamStats }) => {
  const [sortKey, setSortKey] = useState<SortKey>('championProb');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const sortedData = useMemo(() => {
    return [...data].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }

      return sortOrder === 'asc'
        ? (aVal as number) - (bVal as number)
        : (bVal as number) - (aVal as number);
    });
  }, [data, sortKey, sortOrder]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };

  const sortLabel = (key: SortKey) => (sortKey === key ? (sortOrder === 'asc' ? ' ↑' : ' ↓') : '');

  const thClass =
    'cursor-pointer px-2 py-2 text-left text-[10px] font-medium uppercase tracking-wider text-muted hover:text-primary';

  return (
    <div className="rounded-lg border border-muted/20 bg-surface p-4">
      <h3 className="mb-4 text-xs font-medium uppercase tracking-widest text-muted">
        All teams
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-muted/20">
              <th className={thClass} onClick={() => handleSort('rank')}>#{sortLabel('rank')}</th>
              <th className="px-2 py-2 text-left text-[10px] font-medium uppercase tracking-wider text-muted">Flag</th>
              <th className={thClass} onClick={() => handleSort('team')}>Team{sortLabel('team')}</th>
              <th className={thClass} onClick={() => handleSort('qualifyProb')}>
                Qualify{sortLabel('qualifyProb')}
              </th>
              <th className={thClass} onClick={() => handleSort('championProb')}>
                Champ{sortLabel('championProb')}
              </th>
              <th className={thClass} onClick={() => handleSort('elo')}>Elo{sortLabel('elo')}</th>
              <th className="px-2 py-2 text-left text-[10px] font-medium uppercase tracking-wider text-muted">Form</th>
              <th className={thClass} onClick={() => handleSort('attack')}>Atk{sortLabel('attack')}</th>
              <th className={thClass} onClick={() => handleSort('defense')}>Def{sortLabel('defense')}</th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((row) => (
              <tr key={row.team} className="border-b border-muted/10 hover:bg-background">
                <td className="px-2 py-2 tabular-nums text-muted">{row.rank}</td>
                <td className="px-2 py-2">
                  <FlagTooltip team={row.team} stats={getTeamStats(teamStats, row.team)} />
                </td>
                <td className="px-2 py-2 font-medium text-primary">{row.team}</td>
                <td className="px-2 py-2 tabular-nums text-primary">{(row.qualifyProb * 100).toFixed(2)}%</td>
                <td className="px-2 py-2 tabular-nums text-gold">{(row.championProb * 100).toFixed(2)}%</td>
                <td className="px-2 py-2 tabular-nums text-primary">{row.elo}</td>
                <td className="px-2 py-2 text-muted">{row.form}</td>
                <td className="px-2 py-2 tabular-nums text-muted">{row.attack.toFixed(2)}</td>
                <td className="px-2 py-2 tabular-nums text-muted">{row.defense.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ProbabilityTable;
