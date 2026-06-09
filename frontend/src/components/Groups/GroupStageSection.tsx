import React from 'react';
import GroupTable from './GroupTable';
import { PredictionsData } from '../../types';

interface GroupStageSectionProps {
  data: PredictionsData;
}

const GROUP_ORDER = 'ABCDEFGHIJKL'.split('');

const GroupStageSection: React.FC<GroupStageSectionProps> = ({ data }) => {
  const groupStandings = data.group_standings ?? {};

  return (
    <section>
      <div className="mb-4">
        <h2 className="text-sm font-medium text-primary">Group Stage</h2>
        <p className="mt-1 text-xs text-muted">
          Predicted standings from most common scorelines. Qual% = probability of finishing top 2.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {GROUP_ORDER.map((group) => (
          <GroupTable
            key={group}
            group={group}
            standings={groupStandings[group] ?? []}
            teamStats={data.team_stats ?? {}}
          />
        ))}
      </div>
    </section>
  );
};

export default GroupStageSection;
