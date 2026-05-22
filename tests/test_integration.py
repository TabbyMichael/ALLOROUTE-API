import time
from unittest.mock import MagicMock, patch

import pytest

from apps.trips.domain import (
    Coordinate,
    OptimizationResult,
    RouteMetadata,
    VehicleConfig,
)
from services.trips.trip_planner import TripPlannerService


class TestTripPlannerIntegration:
    """
    Integration tests for the full trip planning pipeline.
    Mocks only the external Routing API.
    """

    @pytest.fixture
    def planner(self, spatial_index):
        # We use a planner with the real spatial index (with sample stations)
        # but mock the routing provider
        mock_routing = MagicMock()
        mock_routing.get_route.return_value = RouteMetadata(
            origin="A",
            destination="B",
            total_distance_miles=800.0,
            total_duration_seconds=30000,
            polyline="encoded_polyline",
        )

        # We need to mock GeometryService too because it depends on external polyline lib
        mock_geometry = MagicMock()
        mock_geometry.decode_polyline.return_value = [
            Coordinate(34.0, -118.0),
            Coordinate(35.0, -117.0),
            Coordinate(36.0, -116.0),
        ]
        mock_geometry.calculate_cumulative_distances.return_value = [0.0, 400.0, 800.0]
        # Important: haversine_distance must return a float for comparisons
        mock_geometry.haversine_distance.return_value = 0.0
        from services.routing.geometry import RouteCheckpoint

        mock_geometry.downsample_route.return_value = [
            RouteCheckpoint(
                coordinate=Coordinate(34.0, -118.0),
                distance_from_start=0,
                cumulative_time=0.0,
            ),
            RouteCheckpoint(
                coordinate=Coordinate(35.0, -117.0),
                distance_from_start=400,
                cumulative_time=0.0,
            ),
            RouteCheckpoint(
                coordinate=Coordinate(36.0, -116.0),
                distance_from_start=800,
                cumulative_time=0.0,
            ),
        ]

        # Fix: Ensure cache returns None by default
        mock_cache = MagicMock()
        mock_cache.get_cached_optimization.return_value = None
        mock_cache.get_cached_route.return_value = None

        return TripPlannerService(
            routing_provider=mock_routing,
            geometry_service=mock_geometry,
            spatial_index=spatial_index,
            cache_service=mock_cache,
        )

    def test_full_pipeline_execution(self, planner, vehicle_config):
        """Verify that the full pipeline from routing to optimization works."""
        result = planner.plan_optimized_trip("Chicago", "Los Angeles", vehicle_config)

        assert isinstance(result, OptimizationResult)
        assert result.route_metadata.total_distance_miles == 800.0
        # Should have results from our sample stations
        # Station B is at (35, -117) which matches one of our checkpoints
        assert result.execution_ms > 0

    def test_performance_benchmark(self, planner, vehicle_config):
        """
        A simple benchmark to ensure the pipeline runs within acceptable limits.
        Senior requirement: Performance validation.
        """
        start_time = time.time()
        iterations = 10
        for _ in range(iterations):
            planner.plan_optimized_trip("A", "B", vehicle_config)

        avg_duration = (time.time() - start_time) / iterations
        # Requirement check: Should be sub-200ms for local processing (mocked routing)
        assert avg_duration < 0.2, f"Average duration {avg_duration}s exceeded limit"
