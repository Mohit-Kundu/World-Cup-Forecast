import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from 'recharts';
import FlagImage from '../FlagImage';
import { ChartDataItem, TeamStats } from '../../types';
import { getFlagUrl } from '../../utils/flags';
import { getTeamStats } from '../../utils/safeData';

interface RoundProbChartProps {
  title: string;
  subtitle?: string;
  data: ChartDataItem[];
  teamStats: Record<string, TeamStats>;
  qualifyProbs: Record<string, number>;
  championProbs: Record<string, number>;
}

interface TeamOverviewTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: ChartDataItem }>;
  teamStats: Record<string, TeamStats>;
  qualifyProbs: Record<string, number>;
  championProbs: Record<string, number>;
}

function StatCell({ label, value, valueClassName = 'text-primary' }: {
  label: string;
  value: string | number;
  valueClassName?: string;
}) {
  return (
    <div className="flex items-baseline justify-between gap-2 text-[11px]">
      <span className="text-muted">{label}</span>
      <span className={`tabular-nums font-medium ${valueClassName}`}>{value}</span>
    </div>
  );
}

function TeamOverviewTooltip({
  active,
  payload,
  teamStats,
  qualifyProbs,
  championProbs,
}: TeamOverviewTooltipProps) {
  if (!active || !payload?.length) return null;

  const team = payload[0].payload.team as string;
  const stats = getTeamStats(teamStats, team);
  const qualifyProb = qualifyProbs[team] ?? 0;
  const championProb = championProbs[team] ?? 0;
  const elo = parseInt(stats['FIFA ELO Rating'] ?? '1500', 10) || 1500;
  const form = stats['Recent Form (W5)'] ?? '—';
  const attack = parseFloat(stats['Attack Strength (Avg Goals)'] ?? '0') || 0;
  const defense = parseFloat(stats['Defense Rating (Inverse)'] ?? '0') || 0;

  return (
    <div className="min-w-[15rem] rounded-md border border-muted/30 bg-surface p-3 shadow-xl">
      <p className="mb-2 flex items-center gap-2 border-b border-muted/20 pb-2 text-xs font-medium text-primary">
        <FlagImage team={team} className="h-4 w-6 shrink-0 rounded-sm object-cover ring-1 ring-muted/40" />
        {team}
      </p>
      <div className="grid grid-cols-2 gap-x-4 gap-y-2">
        <StatCell label="Qualify" value={`${(qualifyProb * 100).toFixed(2)}%`} />
        <StatCell label="Champ" value={`${(championProb * 100).toFixed(2)}%`} valueClassName="text-gold" />
        <StatCell label="Elo" value={elo} />
        <StatCell label="Form" value={form} />
        <StatCell label="Atk" value={attack.toFixed(2)} />
        <StatCell label="Def" value={defense.toFixed(2)} />
      </div>
    </div>
  );
}

interface YAxisTickProps {
  x?: number;
  y?: number;
  payload?: { value: string };
}

function YAxisTick({ x = 0, y = 0, payload }: YAxisTickProps): React.ReactElement {
  const team = payload?.value ?? '';

  return (
    <g transform={`translate(${x},${y})`}>
      <foreignObject x={-124} y={-9} width={124} height={18}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: '6px',
            height: '18px',
            fontSize: '11px',
            color: '#D4D8DD',
          }}
        >
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 500 }}>
            {team}
          </span>
          <img
            src={getFlagUrl(team, 40)}
            alt=""
            style={{
              width: '16px',
              height: '12px',
              borderRadius: '2px',
              objectFit: 'cover',
              flexShrink: 0,
            }}
          />
        </div>
      </foreignObject>
    </g>
  );
}

const RoundProbChart: React.FC<RoundProbChartProps> = ({
  title,
  subtitle,
  data,
  teamStats,
  qualifyProbs,
  championProbs,
}) => {
  if (data.length === 0) {
    return (
      <div className="rounded-lg border border-muted/20 bg-surface px-6 py-4">
        <h3 className="text-xs font-medium uppercase tracking-widest text-muted">{title}</h3>
        {subtitle && <p className="mt-1 text-[10px] text-muted">{subtitle}</p>}
        <p className="py-12 text-center text-xs text-muted">No data</p>
      </div>
    );
  }

  const chartHeight = Math.max(280, data.length * 22);

  return (
    <div className="rounded-lg border border-muted/20 bg-surface px-6 py-4">
      <h3 className="text-xs font-medium uppercase tracking-widest text-muted">{title}</h3>
      {subtitle && <p className="mt-1 text-[10px] text-muted">{subtitle}</p>}
      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ left: 4, right: 48, top: 8, bottom: 0 }}
          barCategoryGap="20%"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#3A4A5A" strokeOpacity={0.25} horizontal={false} />
          <XAxis type="number" stroke="#3A4A5A" tick={{ fill: '#3A4A5A', fontSize: 11 }} />
          <YAxis
            type="category"
            dataKey="team"
            stroke="#3A4A5A"
            tick={(props) => <YAxisTick {...props} />}
            width={128}
            interval={0}
          />
          <Tooltip
            cursor={{ fill: 'rgba(191, 160, 70, 0.08)' }}
            content={({ active, payload }) => (
              <TeamOverviewTooltip
                active={active}
                payload={payload as TeamOverviewTooltipProps['payload']}
                teamStats={teamStats}
                qualifyProbs={qualifyProbs}
                championProbs={championProbs}
              />
            )}
          />
          <Bar dataKey="probability" fill="#BFA046" radius={[0, 2, 2, 0]}>
            <LabelList
              dataKey="probability"
              position="right"
              formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
              fill="#D4D8DD"
              fontSize={11}
              fontWeight={400}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RoundProbChart;
