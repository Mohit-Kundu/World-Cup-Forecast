import React from 'react';
import { GroupStandingRow, TeamStats } from '../../types';
import { getTeamStats } from '../../utils/safeData';
import { TEAM_STAT_TOOLTIPS } from '../../utils/teamStatTooltips';
import FlagTooltip from '../FlagTooltip';
import HelpTooltip from '../HelpTooltip';

interface GroupTableProps {
  group: string;
  standings: GroupStandingRow[];
  teamStats: Record<string, TeamStats>;
}

const GroupTable: React.FC<GroupTableProps> = ({ group, standings, teamStats }) => {
  if (standings.length === 0) {
    return (
      <div className="group-stage-card min-w-0 rounded-lg border border-muted/20 bg-surface px-3 py-3 sm:px-4">
        <h3 className="mb-2 text-xs font-medium text-primary">Group {group}</h3>
        <p className="text-[10px] text-muted">No data</p>
      </div>
    );
  }

  return (
    <div className="group-stage-card rounded-lg border border-muted/20 bg-surface px-5 py-3">
      <h3 className="mb-2 text-xs font-medium text-primary">Group {group}</h3>
      <table className="w-full text-[10px]">
        <thead>
          <tr className="border-b border-muted/20">
            <th className="py-1 text-left text-[9px] font-normal uppercase tracking-wider text-muted/70">#</th>
            <th className="py-1 text-left text-[9px] font-normal uppercase tracking-wider text-muted/70" colSpan={2}>Team</th>
            <th className="py-1 text-right text-[9px] font-normal uppercase tracking-wider text-muted/70">Pts</th>
            <th className="py-1 text-right text-[9px] font-normal uppercase tracking-wider text-muted/70">GD</th>
            <th className="py-1 text-right text-[9px] font-normal uppercase tracking-wider text-muted/70">GF</th>
            <th className="py-1 text-right text-[9px] font-normal uppercase tracking-wider text-muted/70">
              <span className="inline-flex items-center justify-end gap-0.5">
                Qual%
                <HelpTooltip text={TEAM_STAT_TOOLTIPS.qualify.tooltip} alignRight />
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          {standings.map((row) => (
            <tr
              key={row.team}
              className={`border-b border-muted/10 ${
                row.rank <= 2 ? 'bg-gold/5' : ''
              }`}
            >
              <td className="py-1.5 font-normal tabular-nums text-primary">{row.rank}</td>
              <td className="py-1.5">
                <FlagTooltip team={row.team} stats={getTeamStats(teamStats, row.team)} />
              </td>
              <td className="max-w-[5.5rem] truncate py-1.5 font-medium text-primary sm:max-w-none">
                {row.team}
              </td>
              <td className="py-1.5 text-right font-normal tabular-nums text-primary">{row.pts}</td>
              <td className="py-1.5 text-right font-normal tabular-nums text-primary">{row.gd > 0 ? `+${row.gd}` : row.gd}</td>
              <td className="py-1.5 text-right font-normal tabular-nums text-primary">{row.gf}</td>
              <td className="py-1.5 text-right font-normal tabular-nums text-gold">
                {(row.qualify_prob * 100).toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default GroupTable;
