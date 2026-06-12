import React from 'react';
import { PredictedFinal } from '../../types';
import FlagImage from '../FlagImage';
import { getTeamColor } from '../../utils/flags';
import FinalOutcomeBar from './FinalOutcomeBar';

interface PredictedFinalCardProps {
  predictedFinal: PredictedFinal;
}

const PredictedFinalCard: React.FC<PredictedFinalCardProps> = ({ predictedFinal }) => {
  const { home_team, away_team, winner, runner_up, pairing_prob, winner_prob } = predictedFinal;
  const winnerColor = getTeamColor(winner);

  if (!home_team || !away_team) {
    return (
      <section>
        <h2 className="mb-4 text-sm font-medium text-primary">Predicted Final</h2>
        <div className="rounded-lg border border-muted/20 bg-surface px-8 py-6 text-center text-xs text-muted">
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

      <div className="rounded-lg border border-muted/20 bg-surface px-8 py-6">
        <div className="space-y-6">
          <div className="text-center">
            <div className="flex items-center justify-center gap-3 text-2xl leading-none md:text-3xl">
              <p className="font-black uppercase tracking-[0.25em] text-gold">
                Winner!
              </p>
              <img
                src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f3c6.svg"
                alt=""
                aria-hidden
                className="h-[calc(1em+2px)] w-[calc(1em+2px)] shrink-0 drop-shadow-[0_0_16px_rgba(191,160,70,0.5)]"
              />
            </div>
            <div className="mt-3 flex justify-center">
              <FlagImage
                team={winner}
                srcWidth={160}
                className="h-10 w-14 rounded-sm object-cover ring-1 ring-gold/40"
              />
            </div>
            <p
              className="mt-3 text-sm font-medium"
              style={{ color: winnerColor }}
            >
              {winner}
            </p>
            <p
              className="mt-1 text-sm tabular-nums"
              style={{ color: winnerColor }}
            >
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
