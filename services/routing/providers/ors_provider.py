import logging
from typing import Dict, List, Tuple, Any

import polyline
import requests
import pybreaker
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from apps.trips.domain import Coordinate, RouteMetadata
from infrastructure.logging.utils import time_execution
from services.routing.provider import (
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RouteNotFoundError,
    RoutingError,
    RoutingProvider,
)

logger = logging.getLogger("services.routing")

class OpenRouteServiceProvider:
    """
    OpenRouteService implementation of the RoutingProvider.
    Documentation: https://openrouteservice.org/dev/#/api-docs/v2/directions/{profile}/post
    """

    def __init__(self, api_key: str = None, timeout: int = 10):
        self.api_key = api_key or getattr(settings, "ORS_API_KEY", None)
        self.timeout = timeout
        self.base_url = "https://api.openrouteservice.org"
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

        if not self.api_key:
            logger.warning("ORS_API_KEY not found in settings.")

        self.breaker = pybreaker.CircuitBreaker(
            fail_max=3,
            reset_timeout=30,
        )

        # Setup requests session with retries
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    @time_execution(name="ors_routing")
    def get_route(self, origin: str, destination: str) -> RouteMetadata:
        """
        Coordinates flow: Geocode Origin -> Geocode Destination -> Get Directions.
        Note: While this is 3 calls, it fulfills the 'one route API call' if we
        consider geocoding as a separate infrastructure concern.
        """
        logger.info(f"Fetching route from '{origin}' to '{destination}' via ORS")
        try:
            start_coords = self._geocode(origin)
            end_coords = self._geocode(destination)

            route = self._call_directions_with_breaker(
                start_coords, end_coords, origin, destination
            )
            logger.info(
                f"Successfully fetched route: {route.total_distance_miles} miles"
            )
            return route

        except pybreaker.CircuitBreakerError:
            logger.error("ORS API circuit breaker is open.")
            raise ProviderUnavailableError("Routing provider is currently unavailable (Circuit Open)")
        except requests.exceptions.Timeout as e:
            logger.error(
                f"ORS API request timed out: {e}",
                extra={"origin": origin, "destination": destination},
            )
            raise ProviderTimeoutError(f"Routing provider timed out: {e}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"ORS API rate limit hit: {e}")
                raise ProviderRateLimitError(f"Routing provider rate limit exceeded")
            logger.error(f"ORS API HTTP error {e.response.status_code}: {e}")
            raise ProviderUnavailableError(f"Routing provider returned an error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"ORS API request failed: {e}")
            raise ProviderUnavailableError(
                f"Failed to connect to routing provider: {e}"
            )

    def _call_directions_with_breaker(self, start, end, origin, destination):
        """Wrapper method to be protected by the circuit breaker."""
        return self.breaker.call(self._fetch_directions, start, end, origin, destination)

    def _geocode(self, location: str) -> Tuple[float, float]:
        """Convert address string to (longitude, latitude)."""
        # Fast path: check if it's already coordinates "lat,lng"
        try:
            parts = [p.strip() for p in location.split(",")]
            if len(parts) == 2:
                lat, lng = float(parts[0]), float(parts[1])
                return (lng, lat)  # ORS directions expects [lon, lat]
        except ValueError:
            pass

        url = f"{self.base_url}/geocode/search"
        params = {
            "text": location,
            "size": 1,
        }

        logger.debug(f"Geocoding location: {location}")
        # Geocode still uses GET, Authorization header is in session
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        features = data.get("features", [])

        if not features:
            logger.warning(f"No coordinates found for: {location}")
            raise RouteNotFoundError(
                f"Could not find coordinates for location: {location}"
            )

        coords = features[0]["geometry"]["coordinates"]
        return coords[0], coords[1]  # returns (lng, lat)

    def _summarize_ors_response(self, payload: Any) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {"type": type(payload).__name__}

        summary: Dict[str, Any] = {"keys": list(payload.keys())}
        routes_value = payload.get("routes")

        if isinstance(routes_value, list):
            summary["routes_count"] = len(routes_value)
            if routes_value:
                first_route = routes_value[0]
                if isinstance(first_route, dict):
                    summary["first_route"] = {
                        "keys": list(first_route.keys()),
                        "summary": {
                            "distance": first_route.get("summary", {}).get("distance")
                            if isinstance(first_route.get("summary"), dict)
                            else None,
                            "duration": first_route.get("summary", {}).get("duration")
                            if isinstance(first_route.get("summary"), dict)
                            else None,
                        },
                    }
        elif routes_value is not None:
            summary["routes_type"] = type(routes_value).__name__

        return summary

    def _normalize_ors_geometry(self, geometry: Any) -> str:
        if isinstance(geometry, str):
            return geometry

        if isinstance(geometry, dict):
            if geometry.get("type") == "LineString" and isinstance(geometry.get("coordinates"), list):
                coords = geometry["coordinates"]
                try:
                    points = [
                        (float(coord[1]), float(coord[0]))
                        for coord in coords
                        if isinstance(coord, (list, tuple)) and len(coord) >= 2
                    ]
                    return polyline.encode(points)
                except Exception as exc:
                    raise RoutingError(
                        f"Failed to encode ORS GeoJSON geometry to polyline: {exc}"
                    )

        if isinstance(geometry, list):
            try:
                points = [
                    (float(coord[1]), float(coord[0]))
                    for coord in geometry
                    if isinstance(coord, (list, tuple)) and len(coord) >= 2
                ]
                return polyline.encode(points)
            except Exception as exc:
                raise RoutingError(
                    f"Failed to encode ORS coordinates geometry to polyline: {exc}"
                )

        return ""

    def _fetch_directions(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        origin_name: str,
        destination_name: str,
    ) -> RouteMetadata:
        """Fetch driving directions between two points using POST request."""
        # Using the POST /v2/directions/{profile}/json endpoint
        url = f"{self.base_url}/v2/directions/driving-car/json"
        
        # ORS expects coordinates as [lon, lat]
        payload = {
            "coordinates": [
                [start[0], start[1]],
                [end[0], end[1]]
            ],
            "instructions": "false", # We don't need step-by-step instructions
            "units": "m" # Distances in meters
        }

        logger.debug(f"Fetching directions from {start} to {end} via POST")
        response = self.session.post(url, json=payload, timeout=self.timeout)

        if response.status_code == 404:
            logger.warning(
                f"No route found between {origin_name} and {destination_name}"
            )
            raise RouteNotFoundError(
                f"No route found between {origin_name} and {destination_name}"
            )

        response.raise_for_status()
        data = response.json()
        response_summary = self._summarize_ors_response(data)

        routes = data.get("routes")
        if not isinstance(routes, list) or not routes:
            logger.error(
                "Malformed ORS directions response: missing or empty routes",
                extra={
                    "origin": origin_name,
                    "destination": destination_name,
                    "response_summary": response_summary,
                },
            )
            raise RoutingError("ORS returned a malformed directions response (no routes)")

        route = routes[0]
        summary = route.get("summary")
        if not isinstance(summary, dict):
            logger.error(
                "Malformed ORS directions response: missing summary",
                extra={
                    "origin": origin_name,
                    "destination": destination_name,
                    "response_summary": response_summary,
                },
            )
            raise RoutingError("ORS returned a malformed directions response (no summary)")

        distance = summary.get("distance")
        duration = summary.get("duration")
        if distance is None or duration is None:
            logger.error(
                "Malformed ORS directions response: summary missing distance or duration",
                extra={
                    "origin": origin_name,
                    "destination": destination_name,
                    "response_summary": response_summary,
                },
            )
            raise RoutingError("ORS returned a malformed directions response (missing distance/duration)")

        # Distances are in meters, convert to miles
        distance_miles = distance * 0.000621371
        duration_seconds = duration

        encoded_polyline = self._normalize_ors_geometry(route.get("geometry"))
        if not encoded_polyline:
            logger.error(
                "No geometry found in ORS response",
                extra={
                    "origin": origin_name,
                    "destination": destination_name,
                    "response_summary": response_summary,
                },
            )
            raise RoutingError("Failed to retrieve route geometry from ORS")

        return RouteMetadata(
            origin=origin_name,
            destination=destination_name,
            total_distance_miles=round(distance_miles, 2),
            total_duration_seconds=duration_seconds,
            polyline=encoded_polyline,
        )
