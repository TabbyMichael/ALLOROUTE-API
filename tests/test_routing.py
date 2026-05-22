import pytest
import responses
from django.test import SimpleTestCase

from services.routing.provider import ProviderUnavailableError, RouteNotFoundError
from services.routing.providers.ors_provider import OpenRouteServiceProvider


class RoutingProviderTest(SimpleTestCase):
    def setUp(self):
        self.ors_provider = OpenRouteServiceProvider(api_key="test-key")

    @responses.activate
    def test_ors_get_route_success(self):
        # Mock Geocoding Origin
        responses.add(
            responses.GET,
            "https://api.openrouteservice.org/geocode/search",
            json={"features": [{"geometry": {"coordinates": [-87.6298, 41.8781]}}]},
            status=200,
        )
        # Mock Geocoding Destination
        responses.add(
            responses.GET,
            "https://api.openrouteservice.org/geocode/search",
            json={"features": [{"geometry": {"coordinates": [-104.9903, 39.7392]}}]},
            status=200,
        )
        # Mock Directions
        responses.add(
            responses.GET,
            "https://api.openrouteservice.org/v2/directions/driving-car",
            json={
                "features": [
                    {
                        "geometry": {
                            "coordinates": [[-87.62, 41.87], [-104.99, 39.73]]
                        },
                        "properties": {
                            "segments": [{"distance": 1600000, "duration": 54000}]
                        },
                    }
                ]
            },
            status=200,
        )

        route = self.ors_provider.get_route("Chicago, IL", "Denver, CO")

        self.assertEqual(route.origin, "Chicago, IL")
        self.assertEqual(route.destination, "Denver, CO")
        self.assertGreater(route.total_distance_miles, 0)
        self.assertIsNotNone(route.polyline)

    @responses.activate
    def test_ors_geocode_not_found(self):
        responses.add(
            responses.GET,
            "https://api.openrouteservice.org/geocode/search",
            json={"features": []},
            status=200,
        )

        with self.assertRaises(RouteNotFoundError):
            self.ors_provider.get_route("Unknown Place", "Denver, CO")

    @responses.activate
    def test_ors_provider_error(self):
        responses.add(
            responses.GET,
            "https://api.openrouteservice.org/geocode/search",
            status=500,
        )

        with self.assertRaises(ProviderUnavailableError):
            self.ors_provider.get_route("Chicago, IL", "Denver, CO")
