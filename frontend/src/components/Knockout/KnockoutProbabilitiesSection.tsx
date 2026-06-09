import React, { useMemo } from 'react';
import RoundProbChart from './RoundProbChart';
import { PredictionsData } from '../../types';
import { probsToChartData } from '../../utils/safeData';

interface KnockoutProbabilitiesSectionProps {
  data: PredictionsData;
}

const KnockoutProbabilitiesSection: React.FC<KnockoutProbabilitiesSectionProps> = ({ data }) => {
  const rounds = useMemo(
    () => [
      {
        title: 'Round of 32',
        subtitle: 'P(win R32 match and advance)',
        data: probsToChartData(data.r32_probs ?? {}),
      },
      {
        title: 'Round of 16',
        subtitle: 'P(win R16 match and advance)',
        data: probsToChartData(data.r16_probs ?? {}),
      },
      {
        title: 'Quarter-Finals',
        subtitle: 'P(win QF match and advance)',
        data: probsToChartData(data.qf_probs ?? {}),
      },
      {
        title: 'Semi-Finals',
        subtitle: 'P(win SF match and reach final)',
        data: probsToChartData(data.sf_probs ?? {}),
      },
      {
        title: 'Final',
        subtitle: 'P(win World Cup)',
        data: probsToChartData(data.champion_probs ?? {}),
      },
    ],
    [data]
  );

  return (
    <section>
      <div className="mb-4">
        <h2 className="text-sm font-medium text-primary">Knockout Probabilities</h2>
        <p className="mt-1 text-xs text-muted">
          Chance each team advances past each knockout round across all simulations.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {rounds.map((round) => (
          <RoundProbChart
            key={round.title}
            title={round.title}
            subtitle={round.subtitle}
            data={round.data}
          />
        ))}
      </div>
    </section>
  );
};

export default KnockoutProbabilitiesSection;
