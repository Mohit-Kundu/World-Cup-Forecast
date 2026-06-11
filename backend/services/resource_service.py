import logging
from pathlib import Path

from src.config import OUTPUT_DIR
from src.models import load_models
from src.preprocessing import load_and_preprocess

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
API_OUTPUT_DIR = PROJECT_ROOT / OUTPUT_DIR


class ResourceService:
    """Load and cache ML models and historical data."""

    def __init__(self) -> None:
        self._cached_resources = None

    def preload(self) -> None:
        """Eagerly load resources (called at app startup)."""
        self.get()

    def get(self) -> dict:
        if self._cached_resources is None:
            logger.info("Loading models and data...")
            data_dir = PROJECT_ROOT / "data"
            model_dir = PROJECT_ROOT / "models"

            df_matches, team_hist, elo_dict = load_and_preprocess(str(data_dir))
            models = load_models(str(model_dir))

            self._cached_resources = {
                "df_matches": df_matches,
                "team_hist": team_hist,
                "elo_dict": elo_dict,
                "models": models,
            }
            logger.info("Resources loaded successfully!")
        return self._cached_resources
