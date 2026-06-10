import React, { useState } from 'react';
import GroupStageSection from './components/Groups/GroupStageSection';
import KnockoutProbabilitiesSection from './components/Knockout/KnockoutProbabilitiesSection';
import PredictedFinalCard from './components/Final/PredictedFinalCard';
import StatsSection from './components/Stats/StatsSection';
import { SimulationControl } from './components/SimulationControl';
import { PredictionsData } from './types';

const App: React.FC = () => {
  const [data, setData] = useState<PredictionsData | null>(null);

  return (
    <div className="min-h-screen bg-background text-primary">
      <div className="mx-auto w-full max-w-[100vw] px-4 py-6 md:px-6 md:py-8">
        <header className="mb-6 border-b border-muted/20 pb-6">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="flex items-center gap-2 text-xl font-medium tracking-tight text-primary md:text-2xl">
                <span className="h-2 w-2 shrink-0 rounded-full bg-gold" aria-hidden />
                FIFA World Cup 2026 Prediction Engine
              </h1>
              <p className="mt-1 text-sm text-muted">
                Roll-form features, H2H stats, Elo-calibrated shootouts
              </p>
            </div>
            {data && (
              <div className="flex flex-col items-start gap-1 sm:items-end">
                {data.source === 'pipeline' && (
                  <span className="rounded-full border border-gold/30 bg-gold/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-gold">
                    Pipeline results
                  </span>
                )}
                {data.source === 'live' && (
                  <span className="rounded-full border border-green-500/30 bg-green-500/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-green-400">
                    Live simulation
                  </span>
                )}
                <span className="text-xs tabular-nums text-muted">
                  {data.n_simulations.toLocaleString()} simulations
                </span>
              </div>
            )}
          </div>
        </header>

        <div className="mb-8">
          <SimulationControl onDataLoaded={setData} />
        </div>

        {data && (
          <main className="space-y-16">
            <GroupStageSection data={data} />
            <KnockoutProbabilitiesSection data={data} />
            <PredictedFinalCard predictedFinal={data.predicted_final} />
            <StatsSection data={data} />
          </main>
        )}

        {!data && (
          <div className="flex flex-col items-center justify-center gap-4 py-20">
            <div className="h-12 w-12 rounded-full border-2 border-muted/30 border-t-gold animate-spin" />
            <p className="text-sm text-muted">Waiting for predictions...</p>
            <p className="text-xs text-muted">
              Run simulation above or ensure pipeline output exists
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
