import pytest
from unittest.mock import MagicMock
from apps.trips.domain import Coordinate, FuelStationDTO
from services.fuel.spatial_index import SpatialIndexService
from repositories.fuel_station_repository import FuelStationRepository

@pytest.fixture
def mock_repo():
    repo = MagicMock(spec=FuelStationRepository)
    repo.get_all_stations.return_value = [
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
    return repo

def test_spatial_index_initialization(mock_repo):
    # Reset singleton state for testing if possible, 
    # but here we just test initialization logic.
    service = SpatialIndexService(repository=mock_repo)
    service.refresh_index()
    
    stats = service.get_stats()
    assert stats["station_count"] == 3
    assert stats["is_initialized"] is True

def test_find_nearby_stations(mock_repo):
    service = SpatialIndexService(repository=mock_repo)
    service.refresh_index()
    
    # Chicago area roughly, but using our mock points
    nearby = service.find_nearby_stations(
        Coordinate(latitude=40.0, longitude=-80.0), 
        radius_miles=20.0
    )
    
    # Should find Station 1 and Station 2 (0.1 deg ~ 7 miles)
    # But not Far Station
    assert len(nearby) == 2
    ids = [s.id for s in nearby]
    assert 1 in ids
    assert 2 in ids
    assert 3 not in ids

def test_find_stations_along_corridor(mock_repo):
    service = SpatialIndexService(repository=mock_repo)
    service.refresh_index()
    
    checkpoints = [
        Coordinate(latitude=40.0, longitude=-80.0),
        Coordinate(latitude=45.0, longitude=-90.0),
    ]
    
    stations = service.find_stations_along_corridor(checkpoints, radius_miles=10.0)
    
    # Should find Station 1 (at first checkpoint) and Far Station (at second)
    assert len(stations) >= 2
    ids = [s.id for s in stations]
    assert 1 in ids
    assert 3 in ids
