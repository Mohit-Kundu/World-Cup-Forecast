from backend.services.prediction_service import PredictionService
from backend.services.resource_service import ResourceService
from backend.services.simulation_service import SimulationService

_resource_service = ResourceService()
_prediction_service = PredictionService()
_simulation_service = SimulationService(_resource_service)


def get_resource_service() -> ResourceService:
    return _resource_service


def get_prediction_service() -> PredictionService:
    return _prediction_service


def get_simulation_service() -> SimulationService:
    return _simulation_service
