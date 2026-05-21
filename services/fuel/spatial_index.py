import logging
import numpy as np
from scipy.spatial import KDTree
from typing import List, Tuple, Dict, Optional
import time

from apps.trips.domain import Coordinate, FuelStationDTO
from repositories.fuel_station_repository import FuelStationRepository

logger = logging.getLogger("services.fuel")

class SpatialIndexService:
    """
    In-memory spatial indexing for fuel stations using scipy KDTree.
    Optimized for high-speed radius queries along a route corridor.
    """

    _instance = None
    _tree: Optional[KDTree] = None
    _stations: List[FuelStationDTO] = []
    _last_updated: float = 0

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SpatialIndexService, cls).__new__(cls)
        return cls._instance

    def __init__(self, repository: FuelStationRepository = None):
        self.repository = repository or FuelStationRepository()
        # Initialize only if needed (lazy loading)

    def _ensure_initialized(self):
        """Lazy initialization of the KDTree."""
        if self._tree is None:
            self.refresh_index()

    def refresh_index(self):
        """
        Loads all fuel stations from the database and rebuilds the spatial index.
        """
        logger.info("Rebuilding spatial index for fuel stations...")
        start_time = time.time()
        
        self._stations = self.repository.get_all_stations()
        
        if not self._stations:
            logger.warning("No fuel stations found in the database. Spatial index is empty.")
            return

        # Extract coordinates for the KDTree
        # Scipy KDTree expects an (N, K) array of points
        coords = np.array([
            [s.coordinate.latitude, s.coordinate.longitude] 
            for s in self._stations
        ])
        
        self._tree = KDTree(coords)
        self._last_updated = time.time()
        
        duration = (self._last_updated - start_time) * 1000
        logger.info(f"Spatial index rebuilt with {len(self._stations)} stations in {duration:.2f}ms")

    def find_nearby_stations(
        self, 
        coordinate: Coordinate, 
        radius_miles: float = 10.0
    ) -> List[FuelStationDTO]:
        """
        Finds all fuel stations within a given radius (in miles) of a coordinate.
        Note: Radius in degrees is approximated (1 degree ~ 69 miles).
        """
        self._ensure_initialized()
        if not self._tree:
            return []

        # Convert miles to approximate degrees for the query
        # This is a rough approximation suitable for the US
        radius_degrees = radius_miles / 69.0
        
        indices = self._tree.query_ball_point(
            [coordinate.latitude, coordinate.longitude], 
            radius_degrees
        )
        
        return [self._stations[i] for i in indices]

    def find_stations_along_corridor(
        self, 
        checkpoints: List[Coordinate], 
        radius_miles: float = 5.0
    ) -> List[FuelStationDTO]:
        """
        Efficiently finds candidate stations along a route corridor.
        Uses the KDTree to query multiple points in a single pass.
        """
        self._ensure_initialized()
        if not self._tree or not checkpoints:
            return []

        radius_degrees = radius_miles / 69.0
        
        # Batch query all checkpoints
        checkpoint_coords = np.array([[c.latitude, c.longitude] for c in checkpoints])
        
        # query_ball_point returns a list of lists of indices
        indices_list = self._tree.query_ball_point(checkpoint_coords, radius_degrees)
        
        # Flatten and remove duplicates
        unique_indices = set()
        for indices in indices_list:
            unique_indices.update(indices)
            
        return [self._stations[i] for i in list(unique_indices)]

    def get_stats(self) -> Dict:
        """Returns statistics about the spatial index."""
        return {
            "station_count": len(self._stations),
            "last_updated": self._last_updated,
            "is_initialized": self._tree is not None
        }
