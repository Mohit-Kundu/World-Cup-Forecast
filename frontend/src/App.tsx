import React, { useRef, useState } from 'react';
import GroupStageSection from './components/Groups/GroupStageSection';
import KnockoutProbabilitiesSection from './components/Knockout/KnockoutProbabilitiesSection';
import PredictedFinalCard from './components/Final/PredictedFinalCard';
import StatsSection from './components/Stats/StatsSection';
import WorldCupWrapped from './components/Wrapped/WorldCupWrapped';
import SectionNavbar from './components/SectionNavbar';
import { SimulationControl } from './components/SimulationControl';
import { useIsMonitorLayout } from './hooks/useIsMonitorLayout';
import { useSnapPageIndex } from './hooks/useSnapPageIndex';
import { PredictionsData } from './types';

const SNAP_SECTION_CLASS =
  'box-border flex min-h-full snap-start snap-always flex-col pb-4 pt-1 2xl:py-6';
const SNAP_INNER_CLASS = 'flex min-h-0 w-full flex-1 flex-col';

const App: React.FC = () => {
  const [data, setData] = useState<PredictionsData | null>(null);
  const mainRef = useRef<HTMLElement>(null);
  const isMonitor = useIsMonitorLayout();
  const pageIndex = useSnapPageIndex(mainRef, !!data);

  return (
    <div className="flex h-screen flex-col bg-background text-primary">
      <div className="mx-auto flex w-full max-w-[92rem] min-h-0 flex-1 flex-col px-4 pt-4 sm:px-6 sm:pt-5 md:px-8 lg:px-10 xl:px-12 2xl:px-16">
        <header className="mb-2 shrink-0 border-b border-muted/20 pb-2 2xl:mb-6 2xl:pb-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between 2xl:gap-4">
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
            <SectionNavbar containerRef={mainRef} activeIndex={pageIndex} isMonitor={isMonitor} />
            <main
              ref={mainRef}
              className="min-h-0 flex-1 snap-y snap-mandatory overflow-y-auto scrollbar-hide"
            >
              <div data-snap-section className={SNAP_SECTION_CLASS}>
                <div className={SNAP_INNER_CLASS}>
                  <PredictedFinalCard
                    predictedFinal={data.predicted_final}
                    teamStats={data.team_stats ?? {}}
                    qualifyProbs={data.qualify_probs ?? {}}
                    championProbs={data.champion_probs ?? {}}
                  />
                  {isMonitor && (
                    <div className="mt-8 2xl:mt-10">
                      <WorldCupWrapped data={data} showHeading />
                    </div>
                  )}
                </div>
              </div>
              {!isMonitor && (
                <div data-snap-section className={SNAP_SECTION_CLASS}>
                  <div className={SNAP_INNER_CLASS}>
                    <WorldCupWrapped data={data} showHeading />
                  </div>
                </div>
              )}
              <div data-snap-section className={SNAP_SECTION_CLASS}>
                <div className={SNAP_INNER_CLASS}>
                  <KnockoutProbabilitiesSection data={data} />
                </div>
              </div>
              <div data-snap-section className={SNAP_SECTION_CLASS}>
                <div className={SNAP_INNER_CLASS}>
                  <GroupStageSection data={data} />
                </div>
              </div>
              <div data-snap-section className={SNAP_SECTION_CLASS}>
                <div className={SNAP_INNER_CLASS}>
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
