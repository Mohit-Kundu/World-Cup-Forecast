export type TeamStatKey = 'qualify' | 'champ' | 'elo' | 'form' | 'attack' | 'defense';

export const TEAM_STAT_TOOLTIPS: Record<TeamStatKey, { label: string; tooltip: string }> = {
  qualify: {
    label: 'Qualify',
    tooltip:
      'Monte Carlo % that team finishes top 2 in their group and advances to the Round of 32.',
  },
  champ: {
    label: 'Champ',
    tooltip: 'Monte Carlo % that team wins the entire tournament.',
  },
  elo: {
    label: 'Elo',
    tooltip: 'FIFA ELO rating at tournament start. ~1500 is average; higher is stronger.',
  },
  form: {
    label: 'Form',
    tooltip:
      'Recent form from the last 5 matches. Points are weighted by opponent strength. 0% = all losses, 100% = all wins.',
  },
  attack: {
    label: 'Atk',
    tooltip: 'Attack rating (weighted avg goals scored). Higher means a stronger attack.',
  },
  defense: {
    label: 'Def',
    tooltip: 'Defense rating (inverse of avg goals conceded). Higher means a stronger defense.',
  },
};
