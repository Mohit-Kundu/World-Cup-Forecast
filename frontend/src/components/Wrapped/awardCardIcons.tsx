import {
  ChessKnight,
  Flame,
  Shield,
  Skull,
  Swords,
  Tornado,
  type LucideIcon,
} from 'lucide-react';

export const AWARD_CARD_ICONS: Record<string, LucideIcon> = {
  'dark-horse': ChessKnight,
  'giant-killer': Swords,
  'lethal-attack': Flame,
  fortress: Shield,
  'group-of-death': Skull,
  'group-of-chaos': Tornado,
};

export function getAwardCardIcon(id: string): LucideIcon {
  return AWARD_CARD_ICONS[id] ?? ChessKnight;
}
