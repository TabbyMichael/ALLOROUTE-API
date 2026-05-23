from typing import List

from apps.trips.domain import Coordinate, FuelStationDTO
from repositories.fuel_station_repository import FuelStationRepository


class SpatialIndexService:
    """
    Service for finding fuel stations based on spatial proximity.
    Now delegates directly to the repository to leverage PostGIS capabilities,
    eliminating the need for an in-memory KDTree.
    """

    def __init__(self, repository: FuelStationRepository = None):
        if repository is None:
            # Fallback for simplified instantiation in some contexts
            from repositories.fuel_station_repository import FuelStationRepository

            self.repository = FuelStationRepository()
        else:
            self.repository = repository

    def refresh_index(self):
        """
        Maintained for backward compatibility, but no longer necessary
        as the database handles spatial indexing.
        """
        pass

    def get_stats(self):
        """
        Returns basic stats about the index state.
        """
        return {
            "is_initialized": True,
            "engine": "PostGIS",
        }

    def find_nearby_stations(
        self, coordinate: Coordinate, radius_miles: float
    ) -> List[FuelStationDTO]:
        return self.repository.find_nearby_stations(coordinate, radius_miles)

    def find_stations_along_corridor(
        self, coordinates: List[Coordinate], radius_miles: float = 5.0
    ) -> List[FuelStationDTO]:
        return self.repository.find_stations_along_corridor(coordinates, radius_miles)
