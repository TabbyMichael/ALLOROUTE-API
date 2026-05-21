from unittest.mock import MagicMock
from django.test import SimpleTestCase
from apps.trips.domain import Coordinate, FuelStationDTO
from services.fuel.spatial_index import SpatialIndexService
from repositories.fuel_station_repository import FuelStationRepository

class SpatialIndexTest(SimpleTestCase):
    def setUp(self):
        self.mock_repo = MagicMock(spec=FuelStationRepository)
        self.mock_repo.get_all_stations.return_value = [
            FuelStationDTO(
                id=1, name="Station 1", address="", city="", state="",
                coordinate=Coordinate(latitude=40.0, longitude=-80.0),
                price_per_gallon=3.50
            ),
            FuelStationDTO(
                id=2, name="Station 2", address="", city="", state="",
                coordinate=Coordinate(latitude=40.1, longitude=-80.1),
                price_per_gallon=3.60
            ),
            FuelStationDTO(
                id=3, name="Far Station", address="", city="", state="",
                coordinate=Coordinate(latitude=45.0, longitude=-90.0),
                price_per_gallon=3.70
            ),
        ]
        # Ensure we are using a fresh instance for each test
        SpatialIndexService._instance = None
        self.service = SpatialIndexService(repository=self.mock_repo)
        self.service.refresh_index()

    def test_spatial_index_initialization(self):
        stats = self.service.get_stats()
        self.assertEqual(stats["station_count"], 3)
        self.assertTrue(stats["is_initialized"])

    def test_find_nearby_stations(self):
        nearby = self.service.find_nearby_stations(
            Coordinate(latitude=40.0, longitude=-80.0), 
            radius_miles=20.0
        )
        
        self.assertEqual(len(nearby), 2)
        ids = [s.id for s in nearby]
        self.assertIn(1, ids)
        self.assertIn(2, ids)
        self.assertNotIn(3, ids)

    def test_find_stations_along_corridor(self):
        checkpoints = [
            Coordinate(latitude=40.0, longitude=-80.0),
            Coordinate(latitude=45.0, longitude=-90.0),
        ]
        
        stations = self.service.find_stations_along_corridor(checkpoints, radius_miles=10.0)
        
        self.assertGreaterEqual(len(stations), 2)
        ids = [s.id for s in stations]
        self.assertIn(1, ids)
        self.assertIn(3, ids)
