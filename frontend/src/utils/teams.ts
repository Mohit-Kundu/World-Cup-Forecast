export const WC2026_GROUPS: Record<string, string[]> = {
  A: ['Mexico', 'South Africa', 'South Korea', 'Czechia'],
  B: ['Canada', 'Switzerland', 'Qatar', 'Bosnia and Herzegovina'],
  C: ['Brazil', 'Morocco', 'Scotland', 'Haiti'],
  D: ['United States', 'Paraguay', 'Australia', 'Türkiye'],
  E: ['Germany', 'Ecuador', 'Ivory Coast', 'Curaçao'],
  F: ['Netherlands', 'Sweden', 'Japan', 'Tunisia'],
  G: ['Belgium', 'Egypt', 'Iran', 'New Zealand'],
  H: ['Spain', 'Uruguay', 'Saudi Arabia', 'Cape Verde'],
  I: ['France', 'Senegal', 'Norway', 'Iraq'],
  J: ['Argentina', 'Austria', 'Algeria', 'Jordan'],
  K: ['Portugal', 'Colombia', 'Uzbekistan', 'DR Congo'],
  L: ['England', 'Croatia', 'Ghana', 'Panama'],
};

export const CONFEDERATIONS = ['UEFA', 'CONMEBOL', 'CONCACAF', 'CAF', 'AFC', 'OFC'] as const;
export type Confederation = (typeof CONFEDERATIONS)[number];

const TEAM_TO_CONFEDERATION: Record<string, Confederation> = {
  Mexico: 'CONCACAF',
  'South Africa': 'CAF',
  'South Korea': 'AFC',
  Czechia: 'UEFA',
  Canada: 'CONCACAF',
  Switzerland: 'UEFA',
  Qatar: 'AFC',
  'Bosnia and Herzegovina': 'UEFA',
  Brazil: 'CONMEBOL',
  Morocco: 'CAF',
  Scotland: 'UEFA',
  Haiti: 'CONCACAF',
  'United States': 'CONCACAF',
  Paraguay: 'CONMEBOL',
  Australia: 'AFC',
  Türkiye: 'UEFA',
  Germany: 'UEFA',
  Ecuador: 'CONMEBOL',
  'Ivory Coast': 'CAF',
  Curaçao: 'CONCACAF',
  Netherlands: 'UEFA',
  Sweden: 'UEFA',
  Japan: 'AFC',
  Tunisia: 'CAF',
  Belgium: 'UEFA',
  Egypt: 'CAF',
  Iran: 'AFC',
  'New Zealand': 'OFC',
  Spain: 'UEFA',
  Uruguay: 'CONMEBOL',
  'Saudi Arabia': 'AFC',
  'Cape Verde': 'CAF',
  France: 'UEFA',
  Senegal: 'CAF',
  Norway: 'UEFA',
  Iraq: 'AFC',
  Argentina: 'CONMEBOL',
  Austria: 'UEFA',
  Algeria: 'CAF',
  Jordan: 'AFC',
  Portugal: 'UEFA',
  Colombia: 'CONMEBOL',
  Uzbekistan: 'AFC',
  'DR Congo': 'CAF',
  England: 'UEFA',
  Croatia: 'UEFA',
  Ghana: 'CAF',
  Panama: 'CONCACAF',
};

const TEAM_TO_GROUP: Record<string, string> = Object.fromEntries(
  Object.entries(WC2026_GROUPS).flatMap(([group, teams]) =>
    teams.map((team) => [team, group])
  )
);

export function getTeamGroup(team: string): string {
  return TEAM_TO_GROUP[team] ?? '';
}

export function getTeamConfederation(team: string): Confederation | '' {
  return TEAM_TO_CONFEDERATION[team] ?? '';
}
