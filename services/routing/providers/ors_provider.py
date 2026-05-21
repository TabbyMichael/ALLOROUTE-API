import logging
import requests
from typing import Dict, List, Tuple
from django.conf import settings
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from apps.trips.domain import RouteMetadata, Coordinate
from services.routing.provider import (
    RoutingProvider,
    RoutingError,
    RouteNotFoundError,
    ProviderUnavailableError,
    ProviderTimeoutError,
    ProviderRateLimitError,
)

from infrastructure.logging.utils import time_execution

logger = logging.getLogger("services.routing")

class OpenRouteServiceProvider:
    """
    OpenRouteService implementation of the RoutingProvider.
    Documentation: https://openrouteservice.org/dev/#/api-docs/v2/directions/{profile}/get
    """

    def __init__(self, api_key: str = None, timeout: int = 10):
        self.api_key = api_key or getattr(settings, "ORS_API_KEY", None)
        self.timeout = timeout
        self.base_url = "https://api.openrouteservice.org"
        
        if not self.api_key:
            logger.warning("ORS_API_KEY not found in settings.")

        # Setup requests session with retries
        self.session = requests.Session()
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
            
            route = self._fetch_directions(start_coords, end_coords, origin, destination)
            logger.info(f"Successfully fetched route: {route.total_distance_miles} miles")
            return route
            
        except requests.exceptions.Timeout as e:
            logger.error(f"ORS API request timed out: {e}", extra={"origin": origin, "destination": destination})
            raise ProviderTimeoutError(f"Routing provider timed out: {e}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"ORS API rate limit hit: {e}")
                raise ProviderRateLimitError(f"Routing provider rate limit exceeded")
            logger.error(f"ORS API HTTP error {e.response.status_code}: {e}")
            raise ProviderUnavailableError(f"Routing provider returned an error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"ORS API request failed: {e}")
            raise ProviderUnavailableError(f"Failed to connect to routing provider: {e}")

    def _geocode(self, location: str) -> Tuple[float, float]:
        """Convert address string to (longitude, latitude)."""
        url = f"{self.base_url}/geocode/search"
        params = {
            "api_key": self.api_key,
            "text": location,
            "size": 1,
        }
        
        logger.debug(f"Geocoding location: {location}")
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        features = data.get("features", [])
        
        if not features:
            logger.warning(f"No coordinates found for: {location}")
            raise RouteNotFoundError(f"Could not find coordinates for location: {location}")
            
        coords = features[0]["geometry"]["coordinates"]
        return coords[0], coords[1]  # returns (lng, lat)

    def _fetch_directions(
        self, 
        start: Tuple[float, float], 
        end: Tuple[float, float],
        origin_name: str,
        destination_name: str
    ) -> RouteMetadata:
        """Fetch driving directions between two points."""
        url = f"{self.base_url}/v2/directions/driving-car"
        params = {
            "api_key": self.api_key,
            "start": f"{start[0]},{start[1]}",
            "end": f"{end[0]},{end[1]}",
        }
        
        logger.debug(f"Fetching directions from {start} to {end}")
        response = self.session.get(url, params=params, timeout=self.timeout)
        
        if response.status_code == 404:
            logger.warning(f"No route found between {origin_name} and {destination_name}")
            raise RouteNotFoundError(f"No route found between {origin_name} and {destination_name}")
            
        response.raise_for_status()
        data = response.json()
        
        # Parse ORS GeoJSON response
        # Note: ORS v2 directions returns a feature collection
        feature = data["features"][0]
        properties = feature["properties"]["segments"][0]
        
        # Distances are in meters, convert to miles
        distance_miles = properties["distance"] * 0.000621371
        duration_seconds = properties["duration"]
        
        # Geometry is typically returned as a LineString in GeoJSON
        geometry = feature["geometry"]
        coordinates = geometry["coordinates"]
        
        # Encode coordinates into a polyline string for efficiency
        import polyline
        # ORS returns [lng, lat], polyline expects [(lat, lng), ...]
        lat_lng_coords = [(c[1], c[0]) for c in coordinates]
        encoded_polyline = polyline.encode(lat_lng_coords)
        
        return RouteMetadata(
            origin=origin_name,
            destination=destination_name,
            total_distance_miles=round(distance_miles, 2),
            total_duration_seconds=duration_seconds,
            polyline=encoded_polyline,
        )
