import logging
import time
from typing import Optional

from apps.trips.domain import OptimizationResult, VehicleConfig
from infrastructure.performance.cache_service import CacheService
from services.fuel.candidate_reduction import CandidateReductionService
from services.fuel.optimizer import FuelOptimizerService
from services.fuel.spatial_index import SpatialIndexService
from services.routing.geometry import GeometryService
from services.routing.providers.ors_provider import OpenRouteServiceProvider
from repositories.fuel_station_repository import FuelStationRepository

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
        optimizer_service=None,
        cache_service=None,
    ):
        self.routing_provider = routing_provider or OpenRouteServiceProvider()
        self.geometry_service = geometry_service or GeometryService()
        self.repository = FuelStationRepository()
        self.spatial_index = spatial_index or SpatialIndexService(repository=self.repository)
        self.reduction_service = reduction_service or CandidateReductionService(
            spatial_index=self.spatial_index, geometry_service=self.geometry_service
        )
        self.optimizer_service = optimizer_service or FuelOptimizerService()
        self.cache_service = cache_service or CacheService()

    def plan_optimized_trip(
        self,
        origin: str,
        destination: str,
        vehicle_config: VehicleConfig = VehicleConfig(),
        user=None,
    ) -> OptimizationResult:
        """
        Executes the full optimization pipeline.
        """
        start_time = time.time()

        # 0. Identify User Tier
        user_role = getattr(user, "token_role", "basic")

        # 0. Try Optimization Cache First
        vehicle_params = {
            "range": vehicle_config.max_range_miles,
            "mpg": vehicle_config.miles_per_gallon,
        }
        cached_result = self.cache_service.get_cached_optimization(
            origin, destination, vehicle_params
        )
        if cached_result:
            logger.info(f"Returning cached optimization for {origin} -> {destination}")
            return cached_result

        logger.info(f"Planning optimized trip from '{origin}' to '{destination}' for role: {user_role}")

        # 1. Get Route (Check Cache -> API)
        route_metadata = self.cache_service.get_cached_route(origin, destination)
        if not route_metadata:
            route_metadata = self.routing_provider.get_route(origin, destination)
            self.cache_service.set_cached_route(origin, destination, route_metadata)
        else:
            logger.info(f"Using cached route for {origin} -> {destination}")

        # Tier Enforcement: Basic users limited to 1000 miles
        if user_role == "basic" and route_metadata.total_distance_miles > 1000:
            from apps.common.exceptions import ValidationError

            raise ValidationError(
                f"Basic tier is limited to 1000 miles. This route is {route_metadata.total_distance_miles} miles. Please upgrade to Premium for longer trips.",
                code="tier_limit_exceeded",
            )

        # 2. Process Geometry (Decode and Downsample)
        coordinates = self.geometry_service.decode_polyline(route_metadata.polyline)
        checkpoints = self.geometry_service.downsample_route(
            coordinates, interval_miles=10.0
        )

        # 3. Reduce Candidate Set
        candidates = self.reduction_service.reduce_candidates(
            checkpoints, corridor_radius_miles=10.0, max_candidates_per_segment=5
        )
        logger.debug(
            f"Reduced candidates to {len(candidates)} stations",
            extra={"candidate_count": len(candidates)},
        )

        # 4. Run Optimization Engine
        result = self.optimizer_service.optimize(
            route_metadata, candidates, vehicle_config
        )

        # 5. Attach performance metrics
        execution_ms = (time.time() - start_time) * 1000
        from dataclasses import replace

        final_result = replace(result, execution_ms=round(execution_ms, 2))

        # 6. Cache the final result
        self.cache_service.set_cached_optimization(
            origin, destination, vehicle_params, final_result
        )

        logger.info(
            f"Trip planning complete in {execution_ms:.2f}ms. Total cost: ${final_result.total_fuel_cost}",
            extra={
                "execution_ms": execution_ms,
                "total_cost": final_result.total_fuel_cost,
                "fuel_stops": len(final_result.fuel_stops),
                "origin": origin,
                "destination": destination,
            },
        )

        return final_result
