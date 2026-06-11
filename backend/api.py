"""
FastAPI Backend for FIFA World Cup 2026 Prediction Frontend
============================================================
Serves model predictions and team statistics via REST API.

Endpoints:
  - GET /api/predictions: Full Monte Carlo simulation results
  - POST /api/simulate: Custom simulation with configurable iterations
  - GET /health: Health check endpoint
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.app import create_app
from backend.dependencies import get_resource_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting FastAPI server...")
    get_resource_service().preload()

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
