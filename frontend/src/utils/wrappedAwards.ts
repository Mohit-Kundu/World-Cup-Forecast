import {
  AwardCard,
  FALLBACK_AWARD_CARDS,
  WrappedAwardPayload,
} from '../components/Wrapped/awardCards';
import {
  AWARD_CARD_LABELS,
  AWARD_CARD_STYLES,
} from '../components/Wrapped/awardCardStyles';
import { PredictionsData } from '../types';

const AWARD_CARD_DISPLAY_ORDER = [
  'group-of-death',
  'group-of-chaos',
  'dark-horse',
  'lethal-attack',
  'fortress',
  'giant-killer',
] as const;

const AWARD_CARD_DISPLAY_ORDER_INDEX: Record<string, number> = AWARD_CARD_DISPLAY_ORDER
  .reduce<Record<string, number>>((acc, id, index) => {
    acc[id] = index;
    return acc;
  }, {});

function mergeAwardPayload(payload: WrappedAwardPayload): AwardCard | null {
  const style = AWARD_CARD_STYLES[payload.id];
  const label = AWARD_CARD_LABELS[payload.id];
  if (!style || !label) {
    return null;
  }

  return {
    id: payload.id,
    label,
    bgColor: style.bgColor,
    accentColor: style.accentColor,
    badgeColor: style.badgeColor,
    badgeTextColor: style.badgeTextColor,
    badgeLabel: payload.badgeLabel,
    bigNumber: payload.bigNumber,
    statLabel: payload.statLabel,
    teams: payload.teams,
    teamName: payload.teamName,
    insight: payload.insight,
  };
}

function byDisplayOrder(a: AwardCard, b: AwardCard): number {
  const aOrder = AWARD_CARD_DISPLAY_ORDER_INDEX[a.id] ?? Number.MAX_SAFE_INTEGER;
  const bOrder = AWARD_CARD_DISPLAY_ORDER_INDEX[b.id] ?? Number.MAX_SAFE_INTEGER;
  return aOrder - bOrder;
}

export function resolveAwardCards(data?: PredictionsData): AwardCard[] {
  const apiCards = data?.wrapped_awards ?? [];
  if (apiCards.length === 0) {
    return FALLBACK_AWARD_CARDS;
  }

  const merged = apiCards
    .map((card) => mergeAwardPayload(card))
    .filter((card): card is AwardCard => card !== null);

  return merged.length > 0 ? merged.sort(byDisplayOrder) : FALLBACK_AWARD_CARDS;
}
