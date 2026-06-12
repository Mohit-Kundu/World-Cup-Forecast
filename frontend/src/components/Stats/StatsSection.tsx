import React, { useMemo } from 'react';
import ProbabilityTable from './ProbabilityTable';
import { PredictionsData, TableDataItem } from '../../types';
import { getTeamConfederation, getTeamGroup } from '../../utils/teams';

interface StatsSectionProps {
  data: PredictionsData;
}

const StatsSection: React.FC<StatsSectionProps> = ({ data }) => {
  const champion_probs = data.champion_probs ?? {};
  const qualify_probs = data.qualify_probs ?? {};
  const team_stats = data.team_stats ?? {};

  const tableData: TableDataItem[] = useMemo(() => {
    return Object.keys(team_stats).map((team) => {
      const stats = team_stats[team];
      return {
        rank: 0,
        flag: team,
        team,
        group: getTeamGroup(team),
        confederation: getTeamConfederation(team),
        qualifyProb: qualify_probs[team] || 0,
        championProb: champion_probs[team] || 0,
        elo: parseInt(stats?.['FIFA ELO Rating'] ?? '1500', 10) || 1500,
        form: stats?.['Recent Form (W5)'] ?? '—',
        attack: parseFloat(stats?.['Attack Strength (Avg Goals)'] ?? '0') || 0,
        defense: parseFloat(stats?.['Defense Rating (Inverse)'] ?? '0') || 0,
      };
    });
  }, [champion_probs, qualify_probs, team_stats]);

  return (
    <section>
      <h2 className="mb-6 text-sm font-medium text-primary">Team Overview</h2>
      <ProbabilityTable data={tableData} teamStats={team_stats} />
    </section>
  );
};

export default StatsSection;
