import React from 'react';
import BracketColumn from './BracketColumn';
import MatchCard from './MatchCard';
import ChampionBox from './ChampionBox';
import { PredictionsData } from '../../types';
import { getTeamStats, getTopChampion } from '../../utils/safeData';
import { useBracketFit } from '../../hooks/useBracketFit';

const BRACKET_WIDTH = 1680;
const BRACKET_HEIGHT = 860;

interface BracketViewProps {
  data: PredictionsData;
}

const BracketView: React.FC<BracketViewProps> = ({ data }) => {
  const { containerRef, scale, width, height } = useBracketFit(BRACKET_WIDTH, BRACKET_HEIGHT);
  const matchResults = data.match_results ?? {};
  const teamStats = data.team_stats ?? {};
  const [championTeam, championProb] = getTopChampion(data.champion_probs);

  const leftR32 = Array.from({ length: 8 }, (_, i) => 49 + i);
  const leftR16 = Array.from({ length: 4 }, (_, i) => 65 + i);
  const leftQF = [73, 74];
  const leftSF = [77];
  const rightSF = [78];
  const rightQF = [75, 76];
  const rightR16 = Array.from({ length: 4 }, (_, i) => 69 + i);
  const rightR32 = Array.from({ length: 8 }, (_, i) => 57 + i);

  const scaledHeight = height * scale;

  return (
    <section>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-medium text-primary">Bracket</h2>
        <span className="text-xs text-muted">Hover flags for stats</span>
      </div>

      <div
        ref={containerRef}
        className="w-full overflow-hidden rounded-lg border border-muted/20 bg-surface"
        style={{ height: scaledHeight }}
      >
        <div className="flex w-full justify-center">
          <div
            style={{
              width: width * scale,
              height: scaledHeight,
              overflow: 'hidden',
            }}
          >
            <div
              className="flex items-center justify-between px-5 py-3"
              style={{
                width,
                height,
                transform: `scale(${scale})`,
                transformOrigin: 'top left',
              }}
            >
              <BracketColumn title="R32" matchIds={leftR32} matchResults={matchResults} teamStats={teamStats} />
              <BracketColumn title="R16" matchIds={leftR16} matchResults={matchResults} teamStats={teamStats} />
              <BracketColumn title="QF" matchIds={leftQF} matchResults={matchResults} teamStats={teamStats} />
              <BracketColumn title="SF" matchIds={leftSF} matchResults={matchResults} teamStats={teamStats} />

              <div className="mx-2 flex min-w-[200px] flex-col justify-center">
                <div className="mb-2 text-center text-[10px] font-medium uppercase tracking-widest text-muted">
                  Final
                </div>
                <MatchCard matchId={79} match={matchResults['79'] ?? null} teamStats={teamStats} />
                <ChampionBox
                  champion={championTeam}
                  probability={championProb}
                  stats={getTeamStats(teamStats, championTeam)}
                />
              </div>

              <BracketColumn title="SF" matchIds={rightSF} matchResults={matchResults} teamStats={teamStats} />
              <BracketColumn title="QF" matchIds={rightQF} matchResults={matchResults} teamStats={teamStats} />
              <BracketColumn title="R16" matchIds={rightR16} matchResults={matchResults} teamStats={teamStats} />
              <BracketColumn title="R32" matchIds={rightR32} matchResults={matchResults} teamStats={teamStats} />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default BracketView;
