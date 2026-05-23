from unittest.mock import MagicMock

from django.test import SimpleTestCase

from apps.trips.domain import Coordinate, FuelStationDTO
from repositories.fuel_station_repository import FuelStationRepository
from services.fuel.spatial_index import SpatialIndexService


class SpatialIndexTest(SimpleTestCase):
    def setUp(self):
        self.mock_repo = MagicMock(spec=FuelStationRepository)
        self.sample_dtos = [
            FuelStationDTO(
                id=1,
                name="Station 1",
                address="",
                city="",
                state="",
                coordinate=Coordinate(latitude=40.0, longitude=-80.0),
                price_per_gallon=3.50,
            ),
            FuelStationDTO(
                id=2,
                name="Station 2",
                address="",
                city="",
                state="",
                coordinate=Coordinate(latitude=40.1, longitude=-80.1),
                price_per_gallon=3.60,
            ),
            FuelStationDTO(
                id=3,
                name="Far Station",
                address="",
                city="",
                state="",
                coordinate=Coordinate(latitude=45.0, longitude=-90.0),
                price_per_gallon=3.70,
            ),
        ]
        self.service = SpatialIndexService(repository=self.mock_repo)

    def test_spatial_index_initialization(self):
        stats = self.service.get_stats()
        self.assertTrue(stats["is_initialized"])
        self.assertEqual(stats["engine"], "PostGIS")

    def test_find_nearby_stations(self):
        # Setup mock to return specific stations
        self.mock_repo.find_nearby_stations.return_value = [self.sample_dtos[0], self.sample_dtos[1]]
        
        nearby = self.service.find_nearby_stations(
            Coordinate(latitude=40.0, longitude=-80.0), radius_miles=20.0
        )

        self.assertEqual(len(nearby), 2)
        self.mock_repo.find_nearby_stations.assert_called_once()

    def test_find_stations_along_corridor(self):
        # Setup mock to return specific stations
        self.mock_repo.find_stations_along_corridor.return_value = [self.sample_dtos[0], self.sample_dtos[2]]
        
        checkpoints = [
            Coordinate(latitude=40.0, longitude=-80.0),
            Coordinate(latitude=45.0, longitude=-90.0),
        ]

        stations = self.service.find_stations_along_corridor(
            checkpoints, radius_miles=10.0
        )

        self.assertEqual(len(stations), 2)
        self.mock_repo.find_stations_along_corridor.assert_called_once()
