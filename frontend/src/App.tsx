import React, { useRef, useState } from 'react';
import GroupStageSection from './components/Groups/GroupStageSection';
import KnockoutProbabilitiesSection from './components/Knockout/KnockoutProbabilitiesSection';
import PredictedFinalCard from './components/Final/PredictedFinalCard';
import StatsSection from './components/Stats/StatsSection';
import SectionNavbar from './components/SectionNavbar';
import { SimulationControl } from './components/SimulationControl';
import { useSnapPageIndex } from './hooks/useSnapPageIndex';
import { PredictionsData } from './types';

const App: React.FC = () => {
  const [data, setData] = useState<PredictionsData | null>(null);
  const mainRef = useRef<HTMLElement>(null);
  const pageIndex = useSnapPageIndex(mainRef, !!data);

  return (
    <div className="flex h-screen flex-col bg-background text-primary">
      <div className="mx-auto flex w-full max-w-7xl min-h-0 flex-1 flex-col px-6 pt-6 sm:px-10 md:px-12 lg:px-16 xl:px-20">
        <header className="mb-6 shrink-0 border-b border-muted/20 pb-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="flex items-center gap-2 text-xl font-medium tracking-tight text-primary md:text-2xl">
                <span className="h-2 w-2 shrink-0 rounded-full bg-gold" aria-hidden />
                FIFA World Cup 2026 Prediction Engine
              </h1>
              <p className="mt-1 text-sm text-muted">
                Roll-form features, H2H stats, Elo-calibrated shootouts
              </p>
            </div>
            <SimulationControl onDataLoaded={setData} />
          </div>
        </header>

        {data && (
          <>
            <SectionNavbar containerRef={mainRef} activeIndex={pageIndex} />
            <main
              ref={mainRef}
              className="min-h-0 flex-1 snap-y snap-mandatory overflow-y-auto scrollbar-hide"
            >
              <div
                data-snap-section
                className="flex min-h-full snap-start snap-always items-start pt-0"
              >
                <div className="w-full">
                  <PredictedFinalCard
                    predictedFinal={data.predicted_final}
                    teamStats={data.team_stats ?? {}}
                    qualifyProbs={data.qualify_probs ?? {}}
                    championProbs={data.champion_probs ?? {}}
                  />
                </div>
              </div>
              <div
                data-snap-section
                className="flex min-h-full snap-start snap-always items-start pt-0"
              >
                <div className="w-full">
                  <KnockoutProbabilitiesSection data={data} />
                </div>
              </div>
              <div
                data-snap-section
                className="flex min-h-full snap-start snap-always items-start pt-0"
              >
                <div className="w-full">
                  <GroupStageSection data={data} />
                </div>
              </div>
              <div
                data-snap-section
                className="flex min-h-full snap-start snap-always items-start pt-0"
              >
                <div className="w-full">
                  <StatsSection data={data} />
                </div>
              </div>
            </main>
          </>
        )}

        {!data && (
          <div className="flex flex-col items-center justify-center gap-4 py-20">
            <div className="h-12 w-12 rounded-full border-2 border-muted/30 border-t-gold animate-spin" />
            <p className="text-sm text-muted">Waiting for predictions...</p>
            <p className="text-xs text-muted">
              Run simulation or ensure pipeline output exists
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
