import random
import time
from typing import List

import numpy as np

from apps.trips.domain import Coordinate, FuelStationDTO
from services.fuel.spatial_index import SpatialIndexService


def benchmark_spatial_index(num_stations: int = 50000, num_queries: int = 1000):
    """
    Benchmarks the spatial index performance.
    Simulates a large dataset and measures lookup speeds.
    """
    print(
        f"--- Benchmarking Spatial Index ({num_stations} stations, {num_queries} queries) ---"
    )

    # Generate mock data
    stations = [
        FuelStationDTO(
            id=i,
            name=f"Station {i}",
            address="",
            city="",
            state="",
            coordinate=Coordinate(
                latitude=random.uniform(25, 49), longitude=random.uniform(-125, -67)
            ),
            price_per_gallon=random.uniform(2.5, 5.0),
        )
        for i in range(num_stations)
    ]

    # Setup service with mock data
    service = SpatialIndexService()
    service._stations = stations

    start_rebuild = time.time()
    coords = np.array(
        [[s.coordinate.latitude, s.coordinate.longitude] for s in stations]
    )
    from scipy.spatial import KDTree

    service._tree = KDTree(coords)
    service._last_updated = time.time()
    rebuild_time = (time.time() - start_rebuild) * 1000
    print(f"Rebuild time: {rebuild_time:.2f}ms")

    # Benchmarking single point radius query
    start_queries = time.time()
    for _ in range(num_queries):
        lat = random.uniform(25, 49)
        lng = random.uniform(-125, -67)
        service.find_nearby_stations(
            Coordinate(latitude=lat, longitude=lng), radius_miles=10.0
        )

    total_query_time = (time.time() - start_queries) * 1000
    avg_query_time = total_query_time / num_queries
    print(f"Total radius query time: {total_query_time:.2f}ms")
    print(f"Average radius query time: {avg_query_time:.4f}ms")

    # Benchmarking corridor query (simulating a 3000 mile route with 300 checkpoints)
    route_checkpoints = [
        Coordinate(latitude=random.uniform(25, 49), longitude=random.uniform(-125, -67))
        for _ in range(300)
    ]

    start_corridor = time.time()
    service.find_stations_along_corridor(route_checkpoints, radius_miles=10.0)
    corridor_time = (time.time() - start_corridor) * 1000
    print(f"Route corridor query (300 checkpoints): {corridor_time:.2f}ms")


if __name__ == "__main__":
    # This script would normally be run via manage.py shell or as a standalone script
    # with Django environment setup.
    pass
