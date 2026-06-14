import type { CSSProperties } from 'react';

export const FINAL_WINNER_COLOR = '#FAC775';
export const FINAL_RUNNER_COLOR = '#E8E6DE';

// Saturated bar fills — light text colors read dull as bar backgrounds on dark UI.
export const FINAL_WINNER_BAR_COLOR = '#BFA046';
export const FINAL_RUNNER_BAR_COLOR = '#C8CDD3';

export const FINAL_WINNER_TEXT_GLOW =
  '0 0 10px rgba(250, 199, 117, 0.75), 0 0 24px rgba(250, 199, 117, 0.4), 0 0 42px rgba(191, 160, 70, 0.22)';

export const FINAL_RUNNER_TEXT_GLOW =
  '0 0 8px rgba(232, 230, 222, 0.5), 0 0 18px rgba(232, 230, 222, 0.24)';

export const FINAL_WINNER_BAR_GLOW =
  '0 0 6px rgba(191, 160, 70, 0.75), 0 0 14px rgba(191, 160, 70, 0.45), 0 0 24px rgba(250, 199, 117, 0.22)';

export const FINAL_RUNNER_BAR_GLOW =
  '0 0 5px rgba(200, 205, 211, 0.55), 0 0 10px rgba(200, 205, 211, 0.28)';

export function finalAccentTextStyle(isWinner: boolean, fontWeight?: number): CSSProperties {
  return {
    color: isWinner ? FINAL_WINNER_COLOR : FINAL_RUNNER_COLOR,
    fontWeight: fontWeight ?? (isWinner ? 600 : 500),
    textShadow: isWinner ? FINAL_WINNER_TEXT_GLOW : FINAL_RUNNER_TEXT_GLOW,
  };
}

export function finalBarSegmentStyle(isWinner: boolean): CSSProperties {
  return {
    backgroundColor: isWinner ? FINAL_WINNER_BAR_COLOR : FINAL_RUNNER_BAR_COLOR,
    boxShadow: isWinner ? FINAL_WINNER_BAR_GLOW : FINAL_RUNNER_BAR_GLOW,
  };
}
