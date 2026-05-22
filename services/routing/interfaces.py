from typing import Any, Dict, List, Protocol, Tuple


class RoutingProvider(Protocol):
    def fetch_route_geometry(self, start: str, finish: str) -> Dict[str, Any]:
        """
        Fetches route geometry, total distance, and duration.
        Expected return: {
            "distance_miles": float,
            "duration_hours": float,
            "polyline": str,
            "coordinates": List[Tuple[float, float]]
        }
        """
        ...
