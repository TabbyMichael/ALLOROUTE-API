from typing import Any, Dict, List, Tuple

import polyline
import requests

from .exceptions import LocationNotFoundError, RoutingProviderError


class OpenRouteServiceProvider:
    BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch_route_geometry(self, start: str, finish: str) -> Dict[str, Any]:
        # start/finish are "lat,lng" strings from the frontend
        try:
            s_lat, s_lng = start.split(",")
            e_lat, e_lng = finish.split(",")
        except ValueError:
            raise RoutingProviderError("Invalid coordinate format. Expected 'lat,lng'.")

        params = {
            "api_key": self.api_key,
            "start": f"{s_lng.strip()},{s_lat.strip()}",
            "end": f"{e_lng.strip()},{e_lat.strip()}",
        }

        response = requests.get(self.BASE_URL, params=params, timeout=10)

        if response.status_code == 404:
            raise LocationNotFoundError("Start or finish location not found.")
        if response.status_code != 200:
            raise RoutingProviderError(
                f"API Error: {response.status_code} - {response.text}"
            )

        data = response.json()
        feature = data["features"][0]
        summary = feature["properties"]["summary"]
        geometry = feature["geometry"]["coordinates"]

        return {
            "distance_miles": summary["distance"] * 0.000621371,
            "duration_hours": summary["duration"] / 3600,
            "polyline": feature["geometry"].get("coordinates"),
            "coordinates": [(c[1], c[0]) for c in geometry],  # Convert to (lat, lng)
        }
