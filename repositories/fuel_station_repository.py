from decimal import Decimal
from typing import List, Optional

from apps.fuel.models import FuelStation
from apps.trips.domain import Coordinate, FuelStationDTO


class FuelStationRepository:
    """
    Repository for accessing fuel station data.
    Decouples the business logic from the Django ORM.
    """

    def get_all_stations(self) -> List[FuelStationDTO]:
        """
        Fetches all fuel stations from the database efficiently.
        Uses .only() to limit fields and .iterator() for memory efficiency with large datasets.
        """
        # Limiting fields fetched from DB to only what is needed for the DTO
        stations = FuelStation.objects.only(
            "station_id",
            "name",
            "address",
            "city",
            "state",
            "latitude",
            "longitude",
            "price_per_gallon",
        ).iterator(chunk_size=2000)

        return [self._to_dto(s) for s in stations]

    def get_stations_by_ids(self, station_ids: List[int]) -> List[FuelStationDTO]:
        """
        Fetches specific fuel stations by their IDs with optimized field selection.
        """
        stations = FuelStation.objects.filter(station_id__in=station_ids).only(
            "station_id",
            "name",
            "address",
            "city",
            "state",
            "latitude",
            "longitude",
            "price_per_gallon",
        )
        return [self._to_dto(s) for s in stations]

    def _to_dto(self, station: FuelStation) -> FuelStationDTO:
        return FuelStationDTO(
            id=station.station_id,
            name=station.name,
            address=station.address,
            city=station.city,
            state=station.state,
            coordinate=Coordinate(
                latitude=station.latitude, longitude=station.longitude
            ),
            price_per_gallon=float(station.price_per_gallon),
        )
