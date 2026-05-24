import logging
from typing import List

from apps.trips.domain import FuelStop, OptimizationResult, RouteMetadata, VehicleConfig
from services.fuel.candidate_reduction import CandidateStation

logger = logging.getLogger("services.fuel")


class FuelOptimizerService:
    """
    Optimization engine that determines the best fuel stops along a route.
    Uses a greedy approach with look-ahead to find cheap fuel stations
    within the vehicle's range.
    """

    def optimize(
        self,
        route: RouteMetadata,
        candidates: List[CandidateStation],
        config: VehicleConfig,
    ) -> OptimizationResult:
        """
        Calculates fuel stops to minimize total cost while ensuring the vehicle
        never runs out of fuel.
        """
        total_gallons = route.total_distance_miles / config.miles_per_gallon
        
        # If no stations or route is within range, just calculate base cost
        if not candidates or route.total_distance_miles <= config.max_range_miles:
            # Assume an average fuel price (e.g., $3.50) if no specific station is chosen
            return OptimizationResult(
                route_metadata=route,
                fuel_stops=[],
                total_fuel_cost=round(total_gallons * 3.50, 2),
                total_gallons=round(total_gallons, 2),
                vehicle_config=config,
                candidate_stations=[c.station for c in candidates],
            )

        fuel_stops: List[FuelStop] = []
        total_cost = 0.0
        
        current_distance = 0.0
        remaining_range = config.max_range_miles

        # Sort candidates by distance along route (just in case)
        sorted_candidates = sorted(candidates, key=lambda x: x.distance_along_route)

        last_stop_distance = 0.0

        while (current_distance + remaining_range) < route.total_distance_miles:
            # Find all reachable stations from current position
            reachable = [
                c
                for c in sorted_candidates
                if last_stop_distance
                < c.distance_along_route
                <= (current_distance + remaining_range)
            ]

            if not reachable:
                logger.warning(
                    f"No reachable fuel stations from {current_distance} miles."
                )
                break  # Cannot reach the end

            cheapest_reachable = min(
                reachable, key=lambda x: x.station.price_per_gallon
            )

            stop_distance = cheapest_reachable.distance_along_route
            dist_traveled = stop_distance - current_distance
            remaining_range -= dist_traveled

            gallons_needed = (
                config.max_range_miles - remaining_range
            ) / config.miles_per_gallon
            cost = gallons_needed * cheapest_reachable.station.price_per_gallon

            fuel_stops.append(
                FuelStop(
                    station=cheapest_reachable.station,
                    gallons_to_buy=round(gallons_needed, 2),
                    cost=round(cost, 2),
                    distance_from_start=round(stop_distance, 2),
                    remaining_range_after_refuel=config.max_range_miles,
                )
            )

            total_cost += cost
            current_distance = stop_distance
            remaining_range = config.max_range_miles
            last_stop_distance = stop_distance

        return OptimizationResult(
            route_metadata=route,
            fuel_stops=fuel_stops,
            total_fuel_cost=round(total_cost, 2),
            total_gallons=round(total_gallons, 2),
            vehicle_config=config,
            candidate_stations=[c.station for c in candidates],
        )
