from typing import List, Optional

import numpy as np
from scipy.spatial import KDTree

from apps.trips.domain import Coordinate, FuelStationDTO
from repositories.fuel_station_repository import FuelStationRepository


class SpatialIndexService:
    def __init__(self, repository: FuelStationRepository):
        self.repository = repository
        self._tree: Optional[KDTree] = None
        self._stations: List[FuelStationDTO] = []

    def refresh_index(self):
        stations = self.repository.get_all_stations()
        if not stations:
            self._tree = None
            self._stations = []
            return

        self._stations = stations
        coords = np.array([(s.coordinate.latitude, s.coordinate.longitude) for s in stations])
        self._tree = KDTree(coords)

    def get_stats(self):
        return {
            "station_count": len(self._stations),
            "is_initialized": self._tree is not None,
        }

    def find_nearby_stations(
        self, coordinate: Coordinate, radius_miles: float
    ) -> List[FuelStationDTO]:
        if self._tree is None:
            self.refresh_index()
        if self._tree is None:
            return []

        radius_deg = radius_miles / 69.0
        indices = self._tree.query_ball_point(
            [coordinate.latitude, coordinate.longitude], r=radius_deg
        )
        return [self._stations[i] for i in indices]

    def find_stations_along_corridor(
        self, coordinates: List[Coordinate], radius_miles: float = 5.0
    ) -> List[FuelStationDTO]:
        if self._tree is None:
            self.refresh_index()
        if self._tree is None:
            return []

        station_indices = set()
        radius_deg = radius_miles / 69.0

        for coord in coordinates:
            indices = self._tree.query_ball_point(
                [coord.latitude, coord.longitude], r=radius_deg
            )
            station_indices.update(indices)

        return [self._stations[i] for i in station_indices]
