from pydantic import BaseModel

from src.config import N_SIMULATIONS_API


class SimulationRequest(BaseModel):
    n_simulations: int = N_SIMULATIONS_API
