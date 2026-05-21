import pytest
from apps.trips.domain import Coordinate, RouteMetadata, FuelStationDTO
from services.fuel.optimizer import FuelOptimizerService
from services.fuel.candidate_reduction import CandidateStation
from apps.trips.domain import VehicleConfig
from apps.common.exceptions import BusinessLogicError

class TestFuelOptimizer:
    """
    Unit tests for the FuelOptimizerService.
    Focuses on the core optimization logic (DP/Graph).
    """

    @pytest.fixture
    def optimizer(self):
        return FuelOptimizerService()

    def _make_candidate(self, id, price, distance):
        station = FuelStationDTO(
            id=id, name=f"S{id}", coordinate=Coordinate(0, 0), 
            price_per_gallon=price, address="", city="", state=""
        )
        return CandidateStation(
            station=station, 
            distance_along_route=distance,
            distance_from_route=0.0
        )

    def test_basic_optimization(self, optimizer, vehicle_config):
        """Test a simple route with a few obvious choices."""
        route = RouteMetadata("Start", "End", 600, 3600, "")
        
        # Station 1: 250 miles in, $3.00
        # Station 2: 500 miles in, $2.50
        candidates = [
            self._make_candidate(1, 3.00, 250.0),
            self._make_candidate(2, 2.50, 500.0),
        ]
        
        result = optimizer.optimize(route, candidates, vehicle_config)
        
        assert result.total_fuel_cost > 0
        assert len(result.fuel_stops) > 0
        # Range is 500. Must stop at least once to reach 600.
        # It's better to stop at station 2 ($2.50) if we can reach it.
        stop_ids = [s.station.id for s in result.fuel_stops]
        assert 2 in stop_ids

    def test_unreachable_destination(self, optimizer, vehicle_config):
        """Verify behavior when the destination is beyond max range and no stations exist."""
        route = RouteMetadata("Start", "End", 1000, 3600, "")
        candidates = [] # No stations
        
        # In current implementation, it returns an empty result if no path is found
        result = optimizer.optimize(route, candidates, vehicle_config)
        assert len(result.fuel_stops) == 0
        assert result.total_fuel_cost == 0

    def test_no_fuel_needed(self, optimizer, vehicle_config):
        """Test case where destination is within initial range."""
        # Vehicle starts with full tank (500 miles range)
        # Destination is 300 miles away.
        # It should reach without any stops.
        route = RouteMetadata("Start", "End", 300, 3600, "")
        candidates = [
            self._make_candidate(1, 1.00, 150.0),
        ]
        
        result = optimizer.optimize(route, candidates, vehicle_config)
        assert len(result.fuel_stops) == 0
        # In our implementation, we calculate total_gallons as total_distance / mpg
        # so total_fuel_cost might be > 0 if we assume consumption cost.
        # Let's check how total_fuel_cost is calculated in optimizer.py
