export const COMPETITIONS = [
  { code: 'PL', name: 'Premier League', country: 'Angleterre', icon: '🏴' },
  { code: 'PD', name: 'La Liga', country: 'Espagne', icon: '🇪🇸' },
  { code: 'BL1', name: 'Bundesliga', country: 'Allemagne', icon: '🇩🇪' },
  { code: 'SA', name: 'Serie A', country: 'Italie', icon: '🇮🇹' },
  { code: 'FL1', name: 'Ligue 1', country: 'France', icon: '🇫🇷' },
  { code: 'CL', name: 'Champions League', country: 'Europe', icon: '🌍' },
]

export const DEFAULT_CODES = COMPETITIONS.map((item) => item.code)
