export type AwardCardStyle = {
  bgColor: string;
  accentColor: string;
  badgeColor?: string;
  badgeTextColor?: string;
};

export const AWARD_CARD_STYLES: Record<string, AwardCardStyle> = {
  'dark-horse': {
    bgColor: '#26215C',
    accentColor: '#AFA9EC',
  },
  'giant-killer': {
    bgColor: '#501313',
    accentColor: '#F09595',
  },
  'lethal-attack': {
    bgColor: '#412402',
    accentColor: '#FAC775',
  },
  fortress: {
    bgColor: '#04342C',
    accentColor: '#5DCAA5',
  },
  'group-of-death': {
    bgColor: '#042C53',
    accentColor: '#85B7EB',
    badgeColor: '#185FA5',
    badgeTextColor: '#B5D4F4',
  },
  'group-of-chaos': {
    bgColor: '#4B1528',
    accentColor: '#ED93B1',
    badgeColor: '#993556',
    badgeTextColor: '#F4C0D1',
  },
};

export const AWARD_CARD_LABELS: Record<string, string> = {
  'dark-horse': 'Dark horse',
  'giant-killer': 'Giant killer',
  'lethal-attack': 'Most lethal attack',
  fortress: 'Fortress defense',
  'group-of-death': 'Group of death',
  'group-of-chaos': 'Group of chaos',
};
