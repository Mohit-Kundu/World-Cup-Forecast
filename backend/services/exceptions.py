class PredictionsNotFoundError(Exception):
    """Raised when no predictions.json snapshot exists."""


class SimulationValidationError(Exception):
    """Raised when simulation parameters are out of allowed bounds."""
