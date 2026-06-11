# FIFA World Cup 2026 Prediction - Quick Start Guide

Get the React frontend up and running in 3 simple steps!

## Prerequisites

- Python 3.8+ installed
- Node.js 16+ and npm installed
- Trained ML models in `models/` directory (run `python main.py` if needed)

## Option 1: Automated Start (Windows PowerShell)

### Start Everything at Once

```powershell
.\start_all.ps1
```

This will:
1. Start the backend server in one window (port 8000)
2. Start the frontend dev server in another window (port 5173)
3. Open both servers automatically

### Or Start Individually

**Backend:**
```powershell
.\start_backend.ps1
```

**Frontend:**
```powershell
.\start_frontend.ps1
```

## Option 2: Manual Start

### Step 1: Start the Backend

```bash
cd backend
pip install -r requirements.txt
python api.py
```

Backend will run at: `http://localhost:8000`
API docs available at: `http://localhost:8000/docs`

### Step 2: Start the Frontend (New Terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend will run at: `http://localhost:5173`

### Step 3: Open Your Browser

Navigate to `http://localhost:5173` to see the app!

## What You'll See

1. **Tournament Bracket**: Interactive knockout stage visualization with all matches from Round of 32 to Final
2. **Team Statistics**: Hover over country flags to see detailed stats (ELO, form, attack/defense ratings)
3. **Champion Predictions**: Charts showing top 15 teams most likely to win
4. **Detailed Leaderboard**: Sortable table with all 48 teams and their statistics

## Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError`
- **Solution**: Install Python dependencies: `pip install -r requirements.txt`

**Error**: `FileNotFoundError: models/`
- **Solution**: Train models first: `python main.py`

### Frontend shows connection error

**Error**: "Failed to load predictions"
- **Solution**: 
  1. Check backend is running: Visit `http://localhost:8000/health`
  2. You should see: `{"status": "healthy", "service": "FIFA WC 2026 Prediction API"}`
  3. If not, restart the backend server

### Port already in use

**Backend (8000)**: Change the port in [`backend/api.py`](backend/api.py):
```python
uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
```

**Frontend (5173)**: Change the port in `frontend/vite.config.ts`:
```typescript
server: {
  port: 5174,
  // ...
}
```

### npm install fails

Try:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

- Explore the interactive bracket
- Hover over flags to see team statistics
- Check the statistics dashboard
- Sort the leaderboard table by different columns

## Customization

### Change Number of Simulations

Default and bounds live in [`src/config.py`](src/config.py):
```python
N_SIMULATIONS_API = 200         # default for POST /api/simulate
N_SIMULATIONS_API_MIN = 10
N_SIMULATIONS_API_MAX = 5_000
```

The frontend can also pass `n_simulations` in the POST `/api/simulate` request body.

### Modify Color Scheme

Edit `frontend/tailwind.config.js`:
```javascript
colors: {
  'deep-navy': '#0b0f19',      // Your custom background
  'accent-indigo': '#818cf8',   // Your custom accent
  // ...
}
```

## API Endpoints

- `GET /api/predictions` - Get all predictions (cached)
- `POST /api/simulate` - Run custom simulation
- `GET /health` - Health check

Visit `http://localhost:8000/docs` for interactive API documentation.

## Performance Tips

- First load may take 10-20 seconds while models initialize
- Subsequent loads are instant due to caching
- Bracket rendering is optimized for 1920px+ displays
- Use horizontal scroll for the full bracket view

## Support

See the detailed documentation:
- Backend: `backend/README.md` (if exists)
- Frontend: `frontend/README.md`
- Full Guide: `README_FRONTEND.md`

Enjoy predicting the World Cup! 🏆⚽
