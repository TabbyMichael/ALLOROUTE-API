from unittest.mock import MagicMock

import pytest
from django.contrib.gis.geos import Point

from apps.fuel.models import FuelStation
from apps.trips.domain import Coordinate, RouteMetadata, VehicleConfig
from services.fuel.spatial_index import SpatialIndexService
from services.routing.geometry import GeometryService


@pytest.fixture
def vehicle_config():
    """Default vehicle configuration."""
    return VehicleConfig(max_range_miles=500.0, miles_per_gallon=10.0)


@pytest.fixture
def mock_route_metadata():
    """Mock route metadata for testing."""
    return RouteMetadata(
        origin="Start City",
        destination="End City",
        total_distance_miles=1000.0,
        total_duration_seconds=36000,
        polyline="encoded_polyline_data",
    )


@pytest.fixture
def sample_stations():
    """A set of sample fuel stations for testing."""
    return [
        FuelStation(
            station_id=1,
            name="Station A",
            location=Point(-118.0, 34.0),
            price_per_gallon=3.50,
            address="Addr A",
            city="City A",
            state="CA",
        ),
        FuelStation(
            station_id=2,
            name="Station B",
            location=Point(-117.0, 35.0),
            price_per_gallon=3.20,
            address="Addr B",
            city="City B",
            state="CA",
        ),
        FuelStation(
            station_id=3,
            name="Station C",
            location=Point(-116.0, 36.0),
            price_per_gallon=3.80,
            address="Addr C",
            city="City C",
            state="CA",
        ),
    ]


@pytest.fixture
def spatial_index(sample_stations):
    """Spatial index service initialized with sample stations."""
    # Mock the repository to return our sample stations
    mock_repo = MagicMock()

    from apps.trips.domain import Coordinate, FuelStationDTO

    dtos = [
        FuelStationDTO(
            id=s.station_id,
            name=s.name,
            address=s.address,
            city=s.city,
            state=s.state,
            coordinate=Coordinate(s.location.y, s.location.x),
            price_per_gallon=float(s.price_per_gallon),
        )
        for s in sample_stations
    ]
    mock_repo.get_all_stations.return_value = dtos

    # Initialize service with mock repo
    service = SpatialIndexService(repository=mock_repo)

    # Reset singleton state for testing
    # Note: SpatialIndexService no longer has _tree or _stations attributes
    service.refresh_index()
    return service


@pytest.fixture
def geometry_service():
    """Geometry service instance."""
    return GeometryService()
