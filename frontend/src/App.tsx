import React from 'react';
import GroupStageSection from './components/Groups/GroupStageSection';
import KnockoutProbabilitiesSection from './components/Knockout/KnockoutProbabilitiesSection';
import PredictedFinalCard from './components/Final/PredictedFinalCard';
import StatsSection from './components/Stats/StatsSection';
import { usePredictions } from './hooks/usePredictions';

const LoadingSpinner: React.FC = () => (
  <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background px-4">
    <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-gold" />
    <div className="text-center">
      <p className="text-sm text-primary">Loading predictions…</p>
    </div>
  </div>
);

const ErrorMessage: React.FC<{ error: string }> = ({ error }) => (
  <div className="flex min-h-screen items-center justify-center bg-background px-4">
    <div className="max-w-md rounded-lg border border-muted/30 bg-surface p-6 text-center">
      <p className="text-sm text-primary">Could not load predictions</p>
      <p className="mt-2 text-xs text-muted">{error}</p>
      <p className="mt-4 text-xs text-muted">
        Backend: <code className="text-primary">python backend/api.py</code>
        <br />
        Frontend: <code className="text-primary">npm run dev</code>
      </p>
      <button
        onClick={() => window.location.reload()}
        className="mt-4 rounded-md border border-muted/50 px-4 py-2 text-xs text-primary transition-colors hover:border-gold hover:text-gold"
      >
        Retry
      </button>
    </div>
  </div>
);

const App: React.FC = () => {
  const { data, loading, error } = usePredictions();

  if (loading) return <LoadingSpinner />;
  if (error || !data) return <ErrorMessage error={error || 'Unknown error'} />;

  return (
    <div className="min-h-screen bg-background text-primary">
      <div className="mx-auto w-full max-w-[100vw] px-4 py-6 md:px-6 md:py-8">
        <header className="mb-10 border-b border-muted/20 pb-6">
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
            <div className="flex flex-col items-start gap-1 sm:items-end">
              {data.source === 'pipeline' && (
                <span className="rounded-full border border-gold/30 bg-gold/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-gold">
                  Pipeline results
                </span>
              )}
              <span className="text-xs tabular-nums text-muted">
                {data.n_simulations.toLocaleString()} simulations
              </span>
            </div>
          </div>
        </header>

        <main className="space-y-16">
          <GroupStageSection data={data} />
          <KnockoutProbabilitiesSection data={data} />
          <PredictedFinalCard predictedFinal={data.predicted_final} />
          <StatsSection data={data} />
        </main>
      </div>
    </div>
  );
};

export default App;
