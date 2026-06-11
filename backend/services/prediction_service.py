from pathlib import Path

from src.predictions_io import load_predictions_json, predictions_json_path

from backend.services.exceptions import PredictionsNotFoundError
from backend.services.resource_service import API_OUTPUT_DIR

PREDICTIONS_NOT_FOUND_MSG = (
    "No predictions snapshot found. "
    "Run pipeline (main.py) or POST to /api/simulate to generate predictions."
)


class PredictionService:
    """Read predictions.json snapshots from the output directory."""

    def __init__(self, output_dir: Path | None = None) -> None:
        self._output_dir = output_dir or API_OUTPUT_DIR

    def get_status(self) -> dict:
        path = predictions_json_path(self._output_dir)
        exists = path.is_file()

        if exists:
            cached = load_predictions_json(self._output_dir)
            if cached:
                return {
                    "has_predictions": True,
                    "source": "pipeline",
                    "n_simulations": cached.get("n_simulations", 0),
                    "path": str(path),
                }

        return {
            "has_predictions": False,
            "source": None,
            "n_simulations": 0,
            "path": str(path),
        }

    def get_predictions(self) -> dict:
        cached = load_predictions_json(self._output_dir)
        if cached is not None:
            return cached

        raise PredictionsNotFoundError(PREDICTIONS_NOT_FOUND_MSG)
