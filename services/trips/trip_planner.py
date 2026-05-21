import logging
import time
from typing import Optional

from apps.trips.domain import OptimizationResult, VehicleConfig
from services.routing.providers.ors_provider import OpenRouteServiceProvider
from services.routing.geometry import GeometryService
from services.fuel.spatial_index import SpatialIndexService
from services.fuel.candidate_reduction import CandidateReductionService
from services.fuel.optimizer import FuelOptimizerService

logger = logging.getLogger("services.trips")

class TripPlannerService:
    """
    Orchestrator for the entire trip optimization pipeline.
    Coordinates between routing, spatial lookups, and the optimization engine.
    """

    def __init__(
        self,
        routing_provider=None,
        geometry_service=None,
        spatial_index=None,
        reduction_service=None,
        optimizer_service=None
    ):
        self.routing_provider = routing_provider or OpenRouteServiceProvider()
        self.geometry_service = geometry_service or GeometryService()
        self.spatial_index = spatial_index or SpatialIndexService()
        self.reduction_service = reduction_service or CandidateReductionService(
            spatial_index=self.spatial_index,
            geometry_service=self.geometry_service
        )
        self.optimizer_service = optimizer_service or FuelOptimizerService()

    def plan_optimized_trip(
        self,
        origin: str,
        destination: str,
        vehicle_config: VehicleConfig = VehicleConfig()
    ) -> OptimizationResult:
        """
        Executes the full optimization pipeline.
        """
        start_time = time.time()
        logger.info(f"Planning optimized trip from '{origin}' to '{destination}'")

        # 1. Get Route from Routing Provider (ONE call)
        route_metadata = self.routing_provider.get_route(origin, destination)

        # 2. Process Geometry (Decode and Downsample)
        coordinates = self.geometry_service.decode_polyline(route_metadata.polyline)
        checkpoints = self.geometry_service.downsample_route(coordinates, interval_miles=10.0)

        # 3. Reduce Candidate Set
        # Use a slightly wider corridor for long trips (e.g. 10 miles)
        candidates = self.reduction_service.reduce_candidates(
            checkpoints,
            corridor_radius_miles=10.0,
            max_candidates_per_segment=5
        )

        # 4. Run Optimization Engine
        result = self.optimizer_service.optimize(
            route_metadata,
            candidates,
            vehicle_config
        )

        # 5. Attach performance metrics
        execution_ms = (time.time() - start_time) * 1000
        
        # Dataclass is frozen, so we use replace if needed or just set if not
        # Since OptimizationResult has execution_ms field, we can't set it if frozen.
        # But wait, my domain.py has execution_ms: Optional[float] = None.
        # Dataclass(frozen=True) means we need to use dacite or just return a new one.
        from dataclasses import replace
        
        final_result = replace(result, execution_ms=round(execution_ms, 2))
        
        logger.info(f"Trip planning complete in {execution_ms:.2f}ms. Total cost: ${final_result.total_fuel_cost}")
        
        return final_result
