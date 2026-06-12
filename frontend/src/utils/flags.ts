export const TEAM_TO_ISO: Record<string, string> = {
  "Mexico": "mx",
  "South Africa": "za",
  "South Korea": "kr",
  "Czechia": "cz",
  "Canada": "ca",
  "Switzerland": "ch",
  "Qatar": "qa",
  "Bosnia and Herzegovina": "ba",
  "Brazil": "br",
  "Morocco": "ma",
  "Scotland": "gb-sct",
  "Haiti": "ht",
  "United States": "us",
  "Paraguay": "py",
  "Australia": "au",
  "Türkiye": "tr",
  "Germany": "de",
  "Ecuador": "ec",
  "Ivory Coast": "ci",
  "Curaçao": "cw",
  "Netherlands": "nl",
  "Sweden": "se",
  "Japan": "jp",
  "Tunisia": "tn",
  "Belgium": "be",
  "Egypt": "eg",
  "Iran": "ir",
  "New Zealand": "nz",
  "Spain": "es",
  "Uruguay": "uy",
  "Saudi Arabia": "sa",
  "Cape Verde": "cv",
  "France": "fr",
  "Senegal": "sn",
  "Norway": "no",
  "Iraq": "iq",
  "Argentina": "ar",
  "Austria": "at",
  "Algeria": "dz",
  "Jordan": "jo",
  "Portugal": "pt",
  "Colombia": "co",
  "Uzbekistan": "uz",
  "DR Congo": "cd",
  "England": "gb-eng",
  "Croatia": "hr",
  "Ghana": "gh",
  "Panama": "pa",
};

export const TEAM_TO_EMOJI: Record<string, string> = {
  "Mexico": "🇲🇽",
  "South Africa": "🇿🇦",
  "South Korea": "🇰🇷",
  "Czechia": "🇨🇿",
  "Canada": "🇨🇦",
  "Switzerland": "🇨🇭",
  "Qatar": "🇶🇦",
  "Bosnia and Herzegovina": "🇧🇦",
  "Brazil": "🇧🇷",
  "Morocco": "🇲🇦",
  "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
  "Haiti": "🇭🇹",
  "United States": "🇺🇸",
  "Paraguay": "🇵🇾",
  "Australia": "🇦🇺",
  "Türkiye": "🇹🇷",
  "Germany": "🇩🇪",
  "Ecuador": "🇪🇨",
  "Ivory Coast": "🇨🇮",
  "Curaçao": "🇨🇼",
  "Netherlands": "🇳🇱",
  "Sweden": "🇸🇪",
  "Japan": "🇯🇵",
  "Tunisia": "🇹🇳",
  "Belgium": "🇧🇪",
  "Egypt": "🇪🇬",
  "Iran": "🇮🇷",
  "New Zealand": "🇳🇿",
  "Spain": "🇪🇸",
  "Uruguay": "🇺🇾",
  "Saudi Arabia": "🇸🇦",
  "Cape Verde": "🇨🇻",
  "France": "🇫🇷",
  "Senegal": "🇸🇳",
  "Norway": "🇳🇴",
  "Iraq": "🇮🇶",
  "Argentina": "🇦🇷",
  "Austria": "🇦🇹",
  "Algeria": "🇩🇿",
  "Jordan": "🇯🇴",
  "Portugal": "🇵🇹",
  "Colombia": "🇨🇴",
  "Uzbekistan": "🇺🇿",
  "DR Congo": "🇨🇩",
  "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  "Croatia": "🇭🇷",
  "Ghana": "🇬🇭",
  "Panama": "🇵🇦",
};

export function getFlagUrl(team: string, width = 80): string {
  const iso = TEAM_TO_ISO[team] || "un";
  return `https://flagcdn.com/w${width}/${iso}.png`;
}

export function getIsoCode(team: string): string {
  return (TEAM_TO_ISO[team] || "??").toUpperCase();
}

export function getEmoji(team: string): string {
  return TEAM_TO_EMOJI[team] || "🏳️";
}

export const TEAM_COLORS: Record<string, string> = {
  "Mexico": "#4A9B7F",
  "South Africa": "#5AA67A",
  "South Korea": "#D66B7A",
  "Czechia": "#C45A5A",
  "Canada": "#CC6666",
  "Switzerland": "#D66B5A",
  "Qatar": "#A85A6B",
  "Bosnia and Herzegovina": "#5A7AB8",
  "Brazil": "#5AB87A",
  "Morocco": "#B85A5A",
  "Scotland": "#5A8AB8",
  "Haiti": "#5A7AB8",
  "United States": "#B86666",
  "Paraguay": "#B85A5A",
  "Australia": "#D4B866",
  "Türkiye": "#D45A5A",
  "Germany": "#CC5A5A",
  "Ecuador": "#D4C866",
  "Ivory Coast": "#D4A85A",
  "Curaçao": "#5A6AB8",
  "Netherlands": "#D48A4A",
  "Sweden": "#5A8AB8",
  "Japan": "#B85A6A",
  "Tunisia": "#CC5A5A",
  "Belgium": "#D45A5A",
  "Egypt": "#C45A5A",
  "Iran": "#6AB87A",
  "New Zealand": "#5A6A8A",
  "Spain": "#B85A5A",
  "Uruguay": "#5A7ACC",
  "Saudi Arabia": "#5A9B6A",
  "Cape Verde": "#5A6AB8",
  "France": "#5A8AB8",
  "Senegal": "#5A9B6A",
  "Norway": "#D45A5A",
  "Iraq": "#B85A5A",
  "Argentina": "#8AB8D4",
  "Austria": "#D45A5A",
  "Algeria": "#5A8B6A",
  "Jordan": "#B85A5A",
  "Portugal": "#5A9B5A",
  "Colombia": "#D4B866",
  "Uzbekistan": "#7AB85A",
  "DR Congo": "#5A9BD4",
  "England": "#B85A66",
  "Croatia": "#D45A5A",
  "Ghana": "#5A8B6A",
  "Panama": "#D45A5A",
};

function popHex(hex: string, satBoost = 1.14, brightBoost = 1.05): string {
  let r = parseInt(hex.slice(1, 3), 16);
  let g = parseInt(hex.slice(3, 5), 16);
  let b = parseInt(hex.slice(5, 7), 16);
  const gray = (r + g + b) / 3;

  r = Math.min(255, Math.round(gray + (r - gray) * satBoost));
  g = Math.min(255, Math.round(gray + (g - gray) * satBoost));
  b = Math.min(255, Math.round(gray + (b - gray) * satBoost));

  r = Math.min(255, Math.round(r * brightBoost));
  g = Math.min(255, Math.round(g * brightBoost));
  b = Math.min(255, Math.round(b * brightBoost));

  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

export function getTeamColor(team: string): string {
  const base = TEAM_COLORS[team];
  return base ? popHex(base) : "#B0B5BA";
}
