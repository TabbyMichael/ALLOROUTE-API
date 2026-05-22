import math
from typing import List, Tuple

import polyline

from apps.trips.domain import Coordinate, RouteCheckpoint


class GeometryService:
    """
    Utilities for processing route geometry and polylines.
    Designed for high performance and low memory footprint.
    """

    @staticmethod
    def decode_polyline(encoded_polyline: str) -> List[Coordinate]:
        """
        Decodes an encoded polyline string into a list of Coordinate objects.
        """
        try:
            coords = polyline.decode(encoded_polyline)
            return [Coordinate(latitude=lat, longitude=lng) for lat, lng in coords]
        except Exception as e:
            raise ValueError(f"Failed to decode polyline: {e}")

    @staticmethod
    def haversine_distance(coord1: Coordinate, coord2: Coordinate) -> float:
        """
        Calculates the great-circle distance between two points on the Earth's surface
        using the Haversine formula. Returns distance in miles.
        """
        R = 3958.8  # Earth radius in miles

        lat1, lon1 = math.radians(coord1.latitude), math.radians(coord1.longitude)
        lat2, lon2 = math.radians(coord2.latitude), math.radians(coord2.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def calculate_cumulative_distances(
        self, coordinates: List[Coordinate]
    ) -> List[float]:
        """
        Calculates the cumulative distance from the start for each coordinate in the list.
        Returns a list of distances in miles.
        """
        if not coordinates:
            return []

        cumulative_distances = [0.0]
        current_distance = 0.0

        for i in range(1, len(coordinates)):
            dist = self.haversine_distance(coordinates[i - 1], coordinates[i])
            current_distance += dist
            cumulative_distances.append(current_distance)

        return cumulative_distances

    def downsample_route(
        self, coordinates: List[Coordinate], interval_miles: float = 10.0
    ) -> List[RouteCheckpoint]:
        """
        Intelligently downsamples the route to provide checkpoints at regular intervals.
        Preserves the start and end points and adapts density based on distance.
        """
        if not coordinates:
            return []

        if len(coordinates) < 2:
            return [
                RouteCheckpoint(
                    coordinate=coordinates[0],
                    distance_from_start=0.0,
                    cumulative_time=0.0,
                )
            ]

        cumulative_distances = self.calculate_cumulative_distances(coordinates)
        total_distance = cumulative_distances[-1]

        checkpoints = []
        # Always include the start
        checkpoints.append(
            RouteCheckpoint(
                coordinate=coordinates[0], distance_from_start=0.0, cumulative_time=0.0
            )
        )

        last_checkpoint_dist = 0.0

        # Iteratively pick points that are roughly 'interval_miles' apart
        for i in range(1, len(coordinates)):
            current_dist = cumulative_distances[i]

            if (current_dist - last_checkpoint_dist) >= interval_miles:
                # Add this point as a checkpoint
                checkpoints.append(
                    RouteCheckpoint(
                        coordinate=coordinates[i],
                        distance_from_start=current_dist,
                        cumulative_time=0.0,  # Time estimation can be added if needed
                    )
                )
                last_checkpoint_dist = current_dist

        # Always ensure the last point is included if it's not already
        if last_checkpoint_dist < total_distance:
            checkpoints.append(
                RouteCheckpoint(
                    coordinate=coordinates[-1],
                    distance_from_start=total_distance,
                    cumulative_time=0.0,
                )
            )

        return checkpoints

    def get_route_corridor_bounds(
        self, coordinates: List[Coordinate], buffer_miles: float = 0.5
    ) -> Tuple[float, float, float, float]:
        """
        Calculates the bounding box (min_lat, min_lng, max_lat, max_lng) of the route
        with a given buffer in miles.
        Approximate degree conversion: 1 degree latitude ~ 69 miles.
        """
        if not coordinates:
            return (0.0, 0.0, 0.0, 0.0)

        lat_buffer = buffer_miles / 69.0
        # Longitude buffer varies by latitude, using a conservative estimate for USA
        lng_buffer = buffer_miles / (
            69.0 * math.cos(math.radians(coordinates[0].latitude))
        )

        min_lat = min(c.latitude for c in coordinates) - lat_buffer
        max_lat = max(c.latitude for c in coordinates) + lat_buffer
        min_lng = min(c.longitude for c in coordinates) - lng_buffer
        max_lng = max(c.longitude for c in coordinates) + lng_buffer

        return (min_lat, min_lng, max_lat, max_lng)
