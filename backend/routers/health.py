from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Landing page for the API — the React app runs separately on port 5173."""
    return {
        "service": "FIFA WC 2026 Prediction API",
        "status": "running",
        "message": "This is the API server. Open the React frontend at http://localhost:5173",
        "endpoints": {
            "health": "/health",
            "predictions": "/api/predictions",
            "simulate": "POST /api/simulate",
            "docs": "/docs",
        },
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "FIFA WC 2026 Prediction API"}
