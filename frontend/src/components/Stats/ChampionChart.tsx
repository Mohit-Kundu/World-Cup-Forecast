import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ChartDataItem } from '../../types';

interface ChampionChartProps {
  data: ChartDataItem[];
}

const ChampionChart: React.FC<ChampionChartProps> = ({ data }) => {
  if (data.length === 0) {
    return (
      <div className="rounded-lg border border-muted/20 bg-surface px-6 py-4">
        <h3 className="mb-4 text-xs font-medium uppercase tracking-widest text-muted">Champion</h3>
        <p className="py-16 text-center text-xs text-muted">No data</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-muted/20 bg-surface px-6 py-4">
      <h3 className="mb-4 text-xs font-medium uppercase tracking-widest text-muted">
        Champion
      </h3>
      <ResponsiveContainer width="100%" height={360}>
        <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20, top: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#3A4A5A" strokeOpacity={0.25} horizontal={false} />
          <XAxis type="number" stroke="#3A4A5A" tick={{ fill: '#3A4A5A', fontSize: 11 }} />
          <YAxis
            type="category"
            dataKey="team"
            stroke="#3A4A5A"
            tick={{ fill: '#D4D8DD', fontSize: 11 }}
            width={96}
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

export default ChampionChart;
