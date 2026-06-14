import { AWARD_CARD_LABELS, AWARD_CARD_STYLES } from './awardCardStyles';

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

export type WrappedAwardPayload = Omit<AwardCard, 'label' | 'bgColor' | 'accentColor' | 'badgeColor' | 'badgeTextColor'>;

export const FALLBACK_AWARD_CARDS: AwardCard[] = [
  {
    id: 'group-of-death',
    label: AWARD_CARD_LABELS['group-of-death'],
    ...AWARD_CARD_STYLES['group-of-death'],
    badgeLabel: 'Group F',
    bigNumber: '2018',
    statLabel: 'avg. ELO across all 4 teams',
    teams: ['Netherlands', 'Japan', 'Sweden', 'Tunisia'],
    insight: 'Netherlands have only 87.6% qual%, their hardest path to R16',
  },
  {
    id: 'group-of-chaos',
    label: AWARD_CARD_LABELS['group-of-chaos'],
    ...AWARD_CARD_STYLES['group-of-chaos'],
    badgeLabel: 'Group D',
    bigNumber: '31%',
    statLabel: 'variance in final standings',
    teams: ['Paraguay', 'United States', 'Australia', 'Türkiye'],
    insight: '3rd place Türkiye (61.1%) has higher qual% than 1st place Paraguay',
  },
  {
    id: 'dark-horse',
    label: AWARD_CARD_LABELS['dark-horse'],
    ...AWARD_CARD_STYLES['dark-horse'],
    bigNumber: '+8.2',
    statLabel: 'spots above their ELO rank',
    teams: ['Japan'],
    teamName: 'Japan',
    insight: 'Model gives them 3.1% champ odds, ELO says 0.9%',
  },
  {
    id: 'lethal-attack',
    label: AWARD_CARD_LABELS['lethal-attack'],
    ...AWARD_CARD_STYLES['lethal-attack'],
    bigNumber: '2.89',
    statLabel: 'expected goals per game',
    teams: ['Spain'],
    teamName: 'Spain',
    insight: 'Only team to avg. 2+ xG against every group opponent',
  },
  {
    id: 'fortress',
    label: AWARD_CARD_LABELS.fortress,
    ...AWARD_CARD_STYLES.fortress,
    bigNumber: '0.64',
    statLabel: 'goals conceded per game',
    teams: ['France'],
    teamName: 'France',
    insight: 'Kept a clean sheet in 58% of all simulated matches',
  },
  {
    id: 'giant-killer',
    label: AWARD_CARD_LABELS['giant-killer'],
    ...AWARD_CARD_STYLES['giant-killer'],
    bigNumber: '4.1',
    statLabel: 'avg. upsets per simulation',
    teams: ['Morocco'],
    teamName: 'Morocco',
    insight: 'Beat higher-ELO opponents in 41% of simulated knockouts',
  },
];

/** @deprecated Use resolveAwardCards() instead. Kept for backward compatibility. */
export const AWARD_CARDS = FALLBACK_AWARD_CARDS;
