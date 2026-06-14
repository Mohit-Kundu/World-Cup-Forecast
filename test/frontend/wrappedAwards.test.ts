import { describe, expect, it } from 'vitest';

import { FALLBACK_AWARD_CARDS } from '@/components/Wrapped/awardCards';
import { AWARD_CARD_LABELS, AWARD_CARD_TOOLTIPS } from '@/components/Wrapped/awardCardStyles';
import { resolveAwardCards } from '@/utils/wrappedAwards';
import { PredictionsData } from '@/types';

const baseData: PredictionsData = {
  match_results: {},
  champion_probs: {},
  finalist_probs: {},
  qualify_probs: {},
  r32_probs: {},
  r16_probs: {},
  qf_probs: {},
  sf_probs: {},
  group_standings: {},
  predicted_final: {
    home_team: '',
    away_team: '',
    winner: '',
    runner_up: '',
    pairing_prob: 0,
    winner_prob: 0,
  },
  team_stats: {},
  n_simulations: 100,
};

describe('resolveAwardCards', () => {
  it('has tooltip copy for every award card', () => {
    for (const id of Object.keys(AWARD_CARD_LABELS)) {
      expect(AWARD_CARD_TOOLTIPS[id]?.length).toBeGreaterThan(0);
    }
  });

  it('returns fallback cards when wrapped_awards is missing', () => {
    expect(resolveAwardCards(undefined)).toEqual(FALLBACK_AWARD_CARDS);
    expect(resolveAwardCards(baseData)).toEqual(FALLBACK_AWARD_CARDS);
  });

  it('merges API payload with static card styling', () => {
    const cards = resolveAwardCards({
      ...baseData,
      wrapped_awards: [
        {
          id: 'dark-horse',
          bigNumber: '+5.0',
          statLabel: 'spots above their ELO rank',
          teams: ['Japan'],
          teamName: 'Japan',
          insight: 'Model likes Japan',
        },
      ],
    });

    expect(cards).toHaveLength(1);
    expect(cards[0].label).toBe('Dark horse');
    expect(cards[0].bgColor).toBe('#26215C');
    expect(cards[0].bigNumber).toBe('+5.0');
    expect(cards[0].teams).toEqual(['Japan']);
  });

  it('applies frontend display order regardless of backend order', () => {
    const cards = resolveAwardCards({
      ...baseData,
      wrapped_awards: [
        { id: 'giant-killer', bigNumber: '0.4', statLabel: 'x', teams: ['Morocco'], insight: 'x' },
        { id: 'fortress', bigNumber: '0.6', statLabel: 'x', teams: ['Spain'], insight: 'x' },
        { id: 'dark-horse', bigNumber: '+2.0', statLabel: 'x', teams: ['Japan'], insight: 'x' },
        { id: 'group-of-chaos', bigNumber: '1.3', statLabel: 'x', teams: ['A', 'B', 'C', 'D'], insight: 'x' },
        { id: 'lethal-attack', bigNumber: '3.1', statLabel: 'x', teams: ['Spain'], insight: 'x' },
        { id: 'group-of-death', bigNumber: '1957', statLabel: 'x', teams: ['A', 'B', 'C', 'D'], insight: 'x' },
      ],
    });

    expect(cards.map((card) => card.id)).toEqual([
      'group-of-death',
      'group-of-chaos',
      'dark-horse',
      'lethal-attack',
      'fortress',
      'giant-killer',
    ]);
  });

  it('falls back when API cards are empty or unknown', () => {
    expect(
      resolveAwardCards({
        ...baseData,
        wrapped_awards: [],
      }),
    ).toEqual(FALLBACK_AWARD_CARDS);

    expect(
      resolveAwardCards({
        ...baseData,
        wrapped_awards: [
          {
            id: 'unknown-card',
            bigNumber: '1',
            statLabel: 'test',
            teams: ['Test'],
            insight: 'test',
          },
        ],
      }),
    ).toEqual(FALLBACK_AWARD_CARDS);
  });
});
