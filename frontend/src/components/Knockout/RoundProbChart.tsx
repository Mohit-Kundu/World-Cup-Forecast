import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ChartDataItem } from '../../types';

interface RoundProbChartProps {
  title: string;
  subtitle?: string;
  data: ChartDataItem[];
}

const RoundProbChart: React.FC<RoundProbChartProps> = ({ title, subtitle, data }) => {
  if (data.length === 0) {
    return (
      <div className="rounded-lg border border-muted/20 bg-surface p-4">
        <h3 className="text-xs font-medium uppercase tracking-widest text-muted">{title}</h3>
        {subtitle && <p className="mt-1 text-[10px] text-muted">{subtitle}</p>}
        <p className="py-12 text-center text-xs text-muted">No data</p>
      </div>
    );
  }

  const chartHeight = Math.max(280, data.length * 22);

  return (
    <div className="rounded-lg border border-muted/20 bg-surface p-4">
      <h3 className="text-xs font-medium uppercase tracking-widest text-muted">{title}</h3>
      {subtitle && <p className="mt-1 text-[10px] text-muted">{subtitle}</p>}
      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ left: 4, right: 20, top: 8, bottom: 0 }}
          barCategoryGap="20%"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#3A4A5A" strokeOpacity={0.25} horizontal={false} />
          <XAxis type="number" stroke="#3A4A5A" tick={{ fill: '#3A4A5A', fontSize: 11 }} />
          <YAxis
            type="category"
            dataKey="team"
            stroke="#3A4A5A"
            tick={{ fill: '#D4D8DD', fontSize: 11 }}
            width={100}
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
          <Bar dataKey="probability" fill="#BFA046" radius={[0, 2, 2, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RoundProbChart;
