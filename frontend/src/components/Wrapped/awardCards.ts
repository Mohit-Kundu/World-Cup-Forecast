export type AwardCard = {
  id: string;
  label: string;
  bgColor: string;
  accentColor: string;
  badgeLabel?: string;
  badgeColor?: string;
  badgeTextColor?: string;
  bigNumber: string;
  statLabel: string;
  teams: string[];
  teamName?: string;
  insight: string;
};

export const AWARD_CARDS: AwardCard[] = [
  {
    id: 'dark-horse',
    label: 'Dark horse',
    bgColor: '#26215C',
    accentColor: '#AFA9EC',
    bigNumber: '+8.2',
    statLabel: 'spots above their ELO rank',
    teams: ['Japan'],
    teamName: 'Japan',
    insight: 'Model gives them 3.1% champ odds, ELO says 0.9%',
  },
  {
    id: 'giant-killer',
    label: 'Giant killer',
    bgColor: '#501313',
    accentColor: '#F09595',
    bigNumber: '4.1',
    statLabel: 'avg. upsets per simulation',
    teams: ['Morocco'],
    teamName: 'Morocco',
    insight: 'Beat higher-ELO opponents in 41% of simulated knockouts',
  },
  {
    id: 'lethal-attack',
    label: 'Most lethal attack',
    bgColor: '#412402',
    accentColor: '#FAC775',
    bigNumber: '2.89',
    statLabel: 'expected goals per game',
    teams: ['Spain'],
    teamName: 'Spain',
    insight: 'Only team to avg. 2+ xG against every group opponent',
  },
  {
    id: 'fortress',
    label: 'Fortress defense',
    bgColor: '#04342C',
    accentColor: '#5DCAA5',
    bigNumber: '0.64',
    statLabel: 'goals conceded per game',
    teams: ['France'],
    teamName: 'France',
    insight: 'Kept a clean sheet in 58% of all simulated matches',
  },
  {
    id: 'group-of-death',
    label: 'Group of death',
    bgColor: '#042C53',
    accentColor: '#85B7EB',
    badgeLabel: 'Group F',
    badgeColor: '#185FA5',
    badgeTextColor: '#B5D4F4',
    bigNumber: '2018',
    statLabel: 'avg. ELO across all 4 teams',
    teams: ['Netherlands', 'Japan', 'Sweden', 'Tunisia'],
    insight: 'Netherlands have only 87.6% qual%, their hardest path to R16',
  },
  {
    id: 'group-of-chaos',
    label: 'Group of chaos',
    bgColor: '#4B1528',
    accentColor: '#ED93B1',
    badgeLabel: 'Group D',
    badgeColor: '#993556',
    badgeTextColor: '#F4C0D1',
    bigNumber: '31%',
    statLabel: 'variance in final standings',
    teams: ['Paraguay', 'United States', 'Australia', 'Türkiye'],
    insight: '3rd place Türkiye (61.1%) has higher qual% than 1st place Paraguay',
  },
];
