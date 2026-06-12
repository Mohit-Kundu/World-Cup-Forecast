import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList } from 'recharts';
import { ChartDataItem } from '../../types';
import { getFlagUrl } from '../../utils/flags';

interface RoundProbChartProps {
  title: string;
  subtitle?: string;
  data: ChartDataItem[];
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

const RoundProbChart: React.FC<RoundProbChartProps> = ({ title, subtitle, data }) => {
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
            contentStyle={{
              backgroundColor: '#171C23',
              border: '1px solid #3A4A5A',
              borderRadius: '6px',
              color: '#D4D8DD',
              fontSize: '12px',
            }}
            formatter={(value: number) => [`${(value * 100).toFixed(2)}%`, 'Prob']}
            labelStyle={{ color: '#D4D8DD' }}
            itemStyle={{ color: '#BFA046' }}
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
