import React from 'react';
import { PredictedFinal, TeamStats } from '../../types';
import FlagImage from '../FlagImage';
import FinalOutcomeBar from './FinalOutcomeBar';
import FinalTeamStats from './FinalTeamStats';
import { FINAL_WINNER_COLOR } from './finalColors';

const FINAL_CARD_CLASS =
  'award-card box-border rounded-xl border border-muted/20 bg-surface';

interface PredictedFinalCardProps {
  predictedFinal: PredictedFinal;
  teamStats: Record<string, TeamStats>;
  qualifyProbs: Record<string, number>;
  championProbs: Record<string, number>;
}

const PredictedFinalCard: React.FC<PredictedFinalCardProps> = ({
  predictedFinal,
  teamStats,
  qualifyProbs,
  championProbs,
}) => {
  const { home_team, away_team, winner, runner_up, pairing_prob, winner_prob } = predictedFinal;
  if (!home_team || !away_team) {
    return (
      <section>
        <h2 className="mb-4 text-sm font-medium text-primary">Predicted Final</h2>
        <div className={`${FINAL_CARD_CLASS} px-8 py-6 text-center text-xs text-muted`}>
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

      <div className={`${FINAL_CARD_CLASS} px-4 py-5 sm:px-6 md:px-8 md:pt-6 md:pb-3`}>
        <div className="space-y-6">
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 text-xl leading-none sm:gap-3 sm:text-2xl md:text-3xl">
              <p
                className="font-black uppercase tracking-[0.25em]"
                style={{ color: FINAL_WINNER_COLOR }}
              >
                Winner!
              </p>
              <FlagImage
                team={winner}
                srcWidth={320}
                loading="eager"
                className="h-6 w-9 shrink-0 rounded-sm object-cover ring-1 ring-[#FAC775]/40 sm:h-7 sm:w-10"
              />
            </div>
          </div>

          <div className="space-y-3">
            <FinalOutcomeBar
              leftTeam={winner}
              rightTeam={runner_up}
              leftProb={winner_prob}
              rightProb={1 - winner_prob}
              leftIsWinner
              rightIsWinner={false}
            />

            <FinalTeamStats
              leftTeam={winner}
              rightTeam={runner_up}
              leftIsWinner
              rightIsWinner={false}
              teamStats={teamStats}
              qualifyProbs={qualifyProbs}
              championProbs={championProbs}
            />
          </div>
        </div>
      </div>
    </section>
  );
};

export default PredictedFinalCard;
