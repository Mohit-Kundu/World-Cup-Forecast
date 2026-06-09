export interface MatchResult {
  home_team: string;
  away_team: string;
  stage: string;
  most_common_home_goals: number;
  most_common_away_goals: number;
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
}

export interface TeamStats {
  "FIFA ELO Rating": string;
  "Recent Form (W5)": string;
  "Attack Strength (Avg Goals)": string;
  "Defense Rating (Inverse)": string;
  "Expected Conceded Goals": string;
  "Discipline Index (Expected Cards)": string;
}

export interface GroupStandingRow {
  team: string;
  rank: number;
  pts: number;
  gd: number;
  gf: number;
  played: number;
  qualify_prob: number;
}

export interface PredictedFinal {
  home_team: string;
  away_team: string;
  winner: string;
  runner_up: string;
  pairing_prob: number;
  winner_prob: number;
}

export interface PredictionsData {
  match_results: Record<string, MatchResult>;
  champion_probs: Record<string, number>;
  finalist_probs: Record<string, number>;
  qualify_probs: Record<string, number>;
  r32_probs: Record<string, number>;
  r16_probs: Record<string, number>;
  qf_probs: Record<string, number>;
  sf_probs: Record<string, number>;
  group_standings: Record<string, GroupStandingRow[]>;
  predicted_final: PredictedFinal;
  team_stats: Record<string, TeamStats>;
  n_simulations: number;
  source?: 'pipeline' | 'live';
}

export interface ChartDataItem {
  team: string;
  probability: number;
}

export interface TableDataItem {
  rank: number;
  flag: string;
  team: string;
  qualifyProb: number;
  championProb: number;
  elo: number;
  form: string;
  attack: number;
  defense: number;
}
