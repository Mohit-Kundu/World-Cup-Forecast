import React from 'react';
import { PredictedFinal } from '../../types';
import FlagImage from '../FlagImage';
import FinalOutcomeBar from './FinalOutcomeBar';

interface PredictedFinalCardProps {
  predictedFinal: PredictedFinal;
}

const PredictedFinalCard: React.FC<PredictedFinalCardProps> = ({ predictedFinal }) => {
  const { home_team, away_team, winner, runner_up, pairing_prob, winner_prob } = predictedFinal;

  if (!home_team || !away_team) {
    return (
      <section>
        <h2 className="mb-4 text-sm font-medium text-primary">Predicted Final</h2>
        <div className="rounded-lg border border-muted/20 bg-surface p-6 text-center text-xs text-muted">
          No final prediction available
        </div>
      </section>
    );
  }

  return (
    <section>
      <div className="mb-4">
        <h2 className="text-sm font-medium text-primary">Predicted Final</h2>
        <p className="mt-1 text-xs text-muted">
          Most common final pairing across simulations ({(pairing_prob * 100).toFixed(1)}% of runs).
        </p>
      </div>

      <div className="rounded-lg border border-muted/20 bg-surface p-6">
        <div className="space-y-6">
          <div className="text-center">
            <p className="text-sm font-bold uppercase tracking-[0.15em] text-gold">Winner!</p>
            <div className="mt-3 flex justify-center">
              <FlagImage
                team={winner}
                className="h-10 w-14 rounded-sm object-cover ring-1 ring-gold/40"
              />
            </div>
            <p className="mt-3 text-sm font-medium text-gold">{winner}</p>
            <p className="mt-1 text-sm tabular-nums text-gold">
              {(winner_prob * 100).toFixed(1)}%
            </p>
          </div>

          <FinalOutcomeBar
            leftTeam={winner}
            rightTeam={runner_up}
            leftProb={winner_prob}
            rightProb={1 - winner_prob}
            leftIsWinner
            rightIsWinner={false}
          />
        </div>
      </div>
    </section>
  );
};

export default PredictedFinalCard;
