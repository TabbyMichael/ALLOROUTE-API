from unittest.mock import MagicMock
from django.test import SimpleTestCase
from apps.trips.domain import Coordinate, FuelStationDTO, RouteCheckpoint
from services.fuel.candidate_reduction import CandidateReductionService, CandidateStation
from services.fuel.spatial_index import SpatialIndexService
from services.routing.geometry import GeometryService

class CandidateReductionTest(SimpleTestCase):
    def setUp(self):
        self.mock_spatial = MagicMock(spec=SpatialIndexService)
        self.mock_geometry = GeometryService() # Use real geometry for distance calcs
        self.service = CandidateReductionService(
            spatial_index=self.mock_spatial,
            geometry_service=self.mock_geometry
        )

    def test_reduce_candidates_logic(self):
        # Setup checkpoints every 10 miles for a 100 mile route
        checkpoints = [
            RouteCheckpoint(Coordinate(0, i/69.0), i, 0) 
            for i in range(0, 101, 10)
        ]
        
        # Setup mock stations
        mock_stations = [
            FuelStationDTO(1, "Cheap 1", "", "", "", Coordinate(0, 5/69.0), 3.00),
            FuelStationDTO(2, "Expensive 1", "", "", "", Coordinate(0.001, 5/69.0), 4.00),
            FuelStationDTO(3, "Cheap 2", "", "", "", Coordinate(0, 55/69.0), 3.10),
            FuelStationDTO(4, "Far Away", "", "", "", Coordinate(1, 1), 3.50),
        ]
        
        self.mock_spatial.find_stations_along_corridor.return_value = mock_stations
        
        # Run reduction (limit 1 per 50 mile segment)
        reduced = self.service.reduce_candidates(
            checkpoints, 
            corridor_radius_miles=5.0,
            max_candidates_per_segment=1
        )
        
        # Should have 2 stations (one for segment 0-50, one for 50-100)
        # Segment 1 (0-50): Station 1 is cheaper than Station 2
        # Segment 2 (50-100): Station 3 is the only one
        # Far Away station might be mapped to segment 2 or excluded depending on corridor
        self.assertEqual(len(reduced), 2)
        
        ids = [c.station.id for c in reduced]
        self.assertIn(1, ids)
        self.assertIn(3, ids)
        self.assertNotIn(2, ids) # Filtered because expensive

    def test_empty_corridor(self):
        self.mock_spatial.find_stations_along_corridor.return_value = []
        checkpoints = [RouteCheckpoint(Coordinate(0,0), 0, 0)]
        
        reduced = self.service.reduce_candidates(checkpoints)
        self.assertEqual(len(reduced), 0)
