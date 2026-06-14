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

export function resolveAwardCards(data?: PredictionsData): AwardCard[] {
  const apiCards = data?.wrapped_awards ?? [];
  if (apiCards.length === 0) {
    return FALLBACK_AWARD_CARDS;
  }

  const merged = apiCards
    .map((card) => mergeAwardPayload(card))
    .filter((card): card is AwardCard => card !== null);

  return merged.length > 0 ? merged : FALLBACK_AWARD_CARDS;
}
