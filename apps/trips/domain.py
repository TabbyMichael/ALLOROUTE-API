from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class Coordinate:
    """Represents a geographic point."""

    latitude: float
    longitude: float


@dataclass(frozen=True)
class VehicleConfig:
    """Configuration for the vehicle's efficiency and capacity."""

    max_range_miles: float = 500.0
    miles_per_gallon: float = 10.0
    tank_capacity_gallons: float = 50.0  # 500 miles / 10 mpg


@dataclass(frozen=True)
class FuelStationDTO:
    """Business layer representation of a fuel station."""

    id: int
    name: str
    address: str
    city: str
    state: str
    coordinate: Coordinate
    price_per_gallon: float


@dataclass(frozen=True)
class RouteCheckpoint:
    """A significant point along the route for optimization decisions."""

    coordinate: Coordinate
    distance_from_start: float
    cumulative_time: float  # in seconds


@dataclass(frozen=True)
class FuelStop:
    """Recommendation for a fuel stop."""

    station: FuelStationDTO
    gallons_to_buy: float
    cost: float
    distance_from_start: float
    remaining_range_after_refuel: float


@dataclass(frozen=True)
class RouteMetadata:
    """Overall metadata for the calculated route."""

    origin: str
    destination: str
    total_distance_miles: float
    total_duration_seconds: float
    polyline: str  # Encoded polyline string


@dataclass(frozen=True)
class OptimizationResult:
    """The final result of the fuel optimization process."""

    route_metadata: RouteMetadata
    fuel_stops: List[FuelStop]
    total_fuel_cost: float
    total_gallons: float
    vehicle_config: VehicleConfig
    generated_at: datetime = field(default_factory=datetime.now)
    execution_ms: Optional[float] = None
