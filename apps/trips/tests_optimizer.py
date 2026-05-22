from django.test import SimpleTestCase

from apps.trips.domain import Coordinate, FuelStationDTO, RouteMetadata, VehicleConfig
from services.fuel.candidate_reduction import CandidateStation
from services.fuel.optimizer import FuelOptimizerService


class FuelOptimizerTest(SimpleTestCase):
    def setUp(self):
        self.service = FuelOptimizerService()
        self.route = RouteMetadata(
            origin="NYC",
            destination="LA",
            total_distance_miles=3000.0,
            total_duration_seconds=150000.0,
            polyline="encoded_polyline",
        )
        self.config = VehicleConfig(max_range_miles=500.0, miles_per_gallon=10.0)

    def test_optimization_basic_path(self):
        # Setup stations every 400 miles
        candidates = [
            CandidateStation(
                station=FuelStationDTO(
                    i, f"Station {i}", "", "", "", Coordinate(0, 0), 3.00
                ),
                distance_along_route=float(i * 400),
                distance_from_route=0.0,
            )
            for i in range(1, 8)  # 400, 800, 1200, 1600, 2000, 2400, 2800
        ]

        result = self.service.optimize(self.route, candidates, self.config)

        self.assertGreater(len(result.fuel_stops), 0)
        self.assertEqual(result.total_gallons, 300.0)  # 3000 miles / 10 mpg
        self.assertLess(result.total_fuel_cost, 1000.0)  # Roughly 300 * 3.00 = 900

        # Verify chronological order
        distances = [s.distance_from_start for s in result.fuel_stops]
        self.assertEqual(distances, sorted(distances))

    def test_optimization_impossible_route(self):
        # No stations, 3000 mile route, 500 mile range
        result = self.service.optimize(self.route, [], self.config)
        self.assertEqual(len(result.fuel_stops), 0)
        self.assertEqual(result.total_fuel_cost, 0.0)

    def test_optimization_prefers_cheaper_stations(self):
        # Two stations reachable from start
        # S1: 400 miles away, $4.00
        # S2: 450 miles away, $3.00
        candidates = [
            CandidateStation(
                station=FuelStationDTO(
                    1, "Expensive", "", "", "", Coordinate(0, 0), 4.00
                ),
                distance_along_route=400.0,
                distance_from_route=0.0,
            ),
            CandidateStation(
                station=FuelStationDTO(2, "Cheap", "", "", "", Coordinate(0, 0), 3.00),
                distance_along_route=450.0,
                distance_from_route=0.0,
            ),
            CandidateStation(
                station=FuelStationDTO(3, "Next", "", "", "", Coordinate(0, 0), 3.00),
                distance_along_route=900.0,
                distance_from_route=0.0,
            ),
            CandidateStation(
                station=FuelStationDTO(4, "End", "", "", "", Coordinate(0, 0), 3.00),
                distance_along_route=1000.0,
                distance_from_route=0.0,
            ),
        ]

        short_route = RouteMetadata("S", "E", 1000.0, 0, "")
        result = self.service.optimize(short_route, candidates, self.config)

        # Should pick the cheap station
        station_ids = [s.station.id for s in result.fuel_stops]
        self.assertIn(2, station_ids)
        self.assertNotIn(1, station_ids)
