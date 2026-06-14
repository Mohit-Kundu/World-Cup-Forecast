import { PredictionsData, TeamStats } from '../types';

export const EMPTY_TEAM_STATS: TeamStats = {
  'FIFA ELO Rating': '—',
  'Recent Form (W5)': '—',
  'Attack Strength (Avg Goals)': '—',
  'Defense Rating (Inverse)': '—',
  'Expected Conceded Goals': '—',
  'Discipline Index (Expected Cards)': '—',
};

export function getTeamStats(
  teamStats: Record<string, TeamStats> | undefined,
  team: string
): TeamStats {
  return teamStats?.[team] ?? EMPTY_TEAM_STATS;
}

export function getTopChampion(
  championProbs: Record<string, number> | undefined
): [string, number] {
  const entries = Object.entries(championProbs ?? {});
  if (entries.length === 0) return ['TBD', 0];
  return entries.reduce((max, curr) => (curr[1] > max[1] ? curr : max));
}

const EMPTY_PREDICTED_FINAL = {
  home_team: '',
  away_team: '',
  winner: '',
  runner_up: '',
  pairing_prob: 0,
  winner_prob: 0,
};

export function normalizePredictions(data: Partial<PredictionsData>): PredictionsData {
  return {
    match_results: data.match_results ?? {},
    champion_probs: data.champion_probs ?? {},
    finalist_probs: data.finalist_probs ?? {},
    qualify_probs: data.qualify_probs ?? {},
    r32_probs: data.r32_probs ?? {},
    r16_probs: data.r16_probs ?? {},
    qf_probs: data.qf_probs ?? {},
    sf_probs: data.sf_probs ?? {},
    group_standings: data.group_standings ?? {},
    predicted_final: data.predicted_final ?? EMPTY_PREDICTED_FINAL,
    team_stats: data.team_stats ?? {},
    wrapped_awards: data.wrapped_awards ?? [],
    n_simulations: data.n_simulations ?? 0,
    source: data.source,
  };
}

export function probsToChartData(
  probs: Record<string, number>,
  limit = 15
): { team: string; probability: number }[] {
  return Object.entries(probs)
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, limit)
    .map(([team, probability]) => ({ team, probability }));
}
