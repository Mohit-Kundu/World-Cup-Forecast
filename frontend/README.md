# FIFA World Cup 2026 Prediction Frontend

Modern React single-page application for visualizing FIFA World Cup 2026 predictions with an interactive tournament bracket and statistics dashboard.

## Features

- **Interactive Tournament Bracket**: View the complete knockout stage progression from Round of 32 to the Final
- **Team Statistics Tooltips**: Hover over country flags to see detailed stats including ELO ratings, form, attack/defense ratings
- **Champion & Finalist Predictions**: Visual charts showing top 15 teams' probabilities
- **Detailed Leaderboard**: Sortable table with all 48 teams and their statistics
- **Dark Modern Theme**: Beautiful gradient design with indigo/purple accents
- **Real-time Data**: Powered by FastAPI backend serving ML model predictions

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Recharts** for data visualizations
- **Axios** for API requests

## Setup & Installation

### Prerequisites

- Node.js 16+ and npm
- Backend server running (see `../backend/`)

### Install Dependencies

```bash
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Bracket/          # Tournament bracket components
│   │   ├── Stats/            # Statistics and charts
│   │   ├── FlagTooltip.tsx   # Reusable flag with tooltip
│   │   └── Header.tsx        # Page header
│   ├── hooks/
│   │   └── usePredictions.ts # Data fetching hook
│   ├── types/
│   │   └── index.ts          # TypeScript interfaces
│   ├── utils/
│   │   └── flags.ts          # Country flag utilities
│   ├── App.tsx               # Main app component
│   ├── main.tsx              # Entry point
│   └── index.css             # Global styles
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## API Integration

The frontend expects the backend API to be running at `http://localhost:8000` with the following endpoint:

- `GET /api/predictions` - Returns match results, champion probabilities, finalist probabilities, and team statistics

## Configuration

Edit `.env` to change the API URL:

```env
VITE_API_URL=http://localhost:8000
```

## Customization

### Colors

Edit `tailwind.config.js` to modify the color scheme:

```javascript
colors: {
  'deep-navy': '#0b0f19',
  'accent-indigo': '#818cf8',
  'accent-purple': '#c084fc',
  'accent-pink': '#f472b6',
  'champion-gold': '#eab308',
  // ... more colors
}
```

### Fonts

The app uses Google Fonts:
- **Outfit** for headings (weight 800)
- **Plus Jakarta Sans** for body text

These are loaded in `index.html`.

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Troubleshooting

### API Connection Issues

If you see "Failed to load predictions":
1. Ensure the backend server is running: `python backend/api.py`
2. Check that the API URL in `.env` is correct
3. Verify CORS is configured properly in the backend

### Build Issues

If you encounter build errors:
1. Delete `node_modules/` and `package-lock.json`
2. Run `npm install` again
3. Clear Vite cache: `npm run dev -- --force`

## License

Part of the FIFA World Cup 2026 Prediction project.
