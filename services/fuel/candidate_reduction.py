import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

from apps.trips.domain import Coordinate, FuelStationDTO, RouteCheckpoint
from infrastructure.logging.utils import time_execution
from services.fuel.spatial_index import SpatialIndexService
from services.routing.geometry import GeometryService

logger = logging.getLogger("services.fuel")


@dataclass(frozen=True)
class CandidateStation:
    """
    A fuel station candidate linked to its position along the route.
    """

    station: FuelStationDTO
    distance_along_route: float
    distance_from_route: float  # Detour distance


class CandidateReductionService:
    """
    Reduces the search space of fuel stations to a minimal, high-quality set
    of candidates for the optimization algorithm.
    """

    def __init__(
        self,
        spatial_index: SpatialIndexService = None,
        geometry_service: GeometryService = None,
    ):
        self.spatial_index = spatial_index or SpatialIndexService()
        self.geometry_service = geometry_service or GeometryService()

    @time_execution(name="candidate_reduction")
    def reduce_candidates(
        self,
        checkpoints: List[RouteCheckpoint],
        corridor_radius_miles: float = 5.0,
        max_candidates_per_segment: int = 5,
    ) -> List[CandidateStation]:
        """
        Main pipeline for candidate reduction.
        1. Find stations in corridor.
        2. Assign to route progress.
        3. Filter/Rank to keep only the most relevant candidates.
        """
        logger.info(
            f"Reducing candidates along route with {len(checkpoints)} checkpoints..."
        )

        # 1. Fetch all stations within the corridor
        checkpoint_coords = [cp.coordinate for cp in checkpoints]
        raw_candidates = self.spatial_index.find_stations_along_corridor(
            checkpoint_coords, radius_miles=corridor_radius_miles
        )

        if not raw_candidates:
            logger.warning("No fuel stations found in the route corridor.")
            return []

        # 2. Map stations to route progress and calculate detour distance
        # We assign each station to its nearest checkpoint to get distance_along_route
        processed_candidates: List[CandidateStation] = []
        for station in raw_candidates:
            # Find nearest checkpoint
            # Optimizing this: for a large number of checkpoints, we could use another KDTree
            # But here we assume checkpoints are manageable (e.g., 200-500)
            nearest_cp, dist_from_route = self._find_nearest_checkpoint(
                station.coordinate, checkpoints
            )

            processed_candidates.append(
                CandidateStation(
                    station=station,
                    distance_along_route=nearest_cp.distance_from_start,
                    distance_from_route=dist_from_route,
                )
            )

        # 3. Sort by distance along route
        processed_candidates.sort(key=lambda x: x.distance_along_route)

        # 4. Filter: Keep only the best candidates per segment to reduce complexity
        # A segment is defined by the max range (e.g., every 50 miles)
        reduced_set = self._filter_best_candidates(
            processed_candidates,
            segment_size_miles=50.0,
            limit_per_segment=max_candidates_per_segment,
        )

        logger.info(
            f"Candidate reduction complete: {len(raw_candidates)} -> {len(reduced_set)}"
        )
        return reduced_set

    def _find_nearest_checkpoint(
        self, coord: Coordinate, checkpoints: List[RouteCheckpoint]
    ) -> Tuple[RouteCheckpoint, float]:
        """
        Finds the nearest checkpoint to a coordinate and the distance to it.
        """
        min_dist = float("inf")
        nearest_cp = checkpoints[0]

        for cp in checkpoints:
            dist = self.geometry_service.haversine_distance(coord, cp.coordinate)
            if dist < min_dist:
                min_dist = dist
                nearest_cp = cp

        return nearest_cp, min_dist

    def _filter_best_candidates(
        self,
        candidates: List[CandidateStation],
        segment_size_miles: float = 50.0,
        limit_per_segment: int = 5,
    ) -> List[CandidateStation]:
        """
        Groups candidates into segments along the route and keeps only the cheapest
        stations in each segment. This dramatically reduces K for the graph algorithm.
        """
        if not candidates:
            return []

        # Group by segment
        segments: Dict[int, List[CandidateStation]] = {}
        for c in candidates:
            segment_idx = int(c.distance_along_route // segment_size_miles)
            if segment_idx not in segments:
                segments[segment_idx] = []
            segments[segment_idx].append(c)

        final_candidates: List[CandidateStation] = []
        for segment_idx in sorted(segments.keys()):
            segment_candidates = segments[segment_idx]

            # Sort by price (cheapest first)
            segment_candidates.sort(key=lambda x: x.station.price_per_gallon)

            # Take the top N
            final_candidates.extend(segment_candidates[:limit_per_segment])

        # Final sort to ensure chronological order
        final_candidates.sort(key=lambda x: x.distance_along_route)
        return final_candidates
