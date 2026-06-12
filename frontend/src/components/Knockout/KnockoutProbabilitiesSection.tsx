import React, { useMemo, useState } from 'react';
import RoundProbChart from './RoundProbChart';
import { PredictionsData } from '../../types';
import { probsToChartData } from '../../utils/safeData';

interface KnockoutProbabilitiesSectionProps {
  data: PredictionsData;
}

const KnockoutProbabilitiesSection: React.FC<KnockoutProbabilitiesSectionProps> = ({ data }) => {
  const [activeRound, setActiveRound] = useState(0);

  const rounds = useMemo(
    () => [
      {
        tab: 'Final',
        title: 'Final',
        subtitle: 'P(win World Cup)',
        data: probsToChartData(data.champion_probs ?? {}),
      },
      {
        tab: 'SF',
        title: 'Semi-Finals',
        subtitle: 'P(win SF match and reach final)',
        data: probsToChartData(data.sf_probs ?? {}),
      },
      {
        tab: 'QF',
        title: 'Quarter-Finals',
        subtitle: 'P(win QF match and advance)',
        data: probsToChartData(data.qf_probs ?? {}),
      },
      {
        tab: 'R16',
        title: 'Round of 16',
        subtitle: 'P(win R16 match and advance)',
        data: probsToChartData(data.r16_probs ?? {}),
      },
      {
        tab: 'R32',
        title: 'Round of 32',
        subtitle: 'P(win R32 match and advance)',
        data: probsToChartData(data.r32_probs ?? {}),
      },
    ],
    [data]
  );

  const selected = rounds[activeRound];

  return (
    <section>
      <div className="mb-4">
        <h2 className="text-sm font-medium text-primary">Knockout Probabilities</h2>
        <p className="mt-1 text-xs text-muted">
          Chance each team advances past each knockout round across all simulations.
        </p>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {rounds.map((round, index) => (
          <button
            key={round.tab}
            type="button"
            onClick={() => setActiveRound(index)}
            className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
              activeRound === index
                ? 'border-gold/50 bg-gold/15 text-gold'
                : 'border-muted/30 bg-surface text-muted hover:border-muted/50 hover:text-primary'
            }`}
          >
            {round.tab}
          </button>
        ))}
      </div>

      <RoundProbChart
        key={selected.title}
        title={selected.title}
        subtitle={selected.subtitle}
        data={selected.data}
      />
    </section>
  );
};

export default KnockoutProbabilitiesSection;
