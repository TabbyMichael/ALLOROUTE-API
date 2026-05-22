from decimal import Decimal
from unittest.mock import MagicMock

import responses
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.fuel.models import FuelStation
from services.fuel.spatial_index import SpatialIndexService


class TripOptimizeAPITest(APITestCase):
    def setUp(self):
        # Create some fuel stations in the database
        FuelStation.objects.create(
            station_id=1,
            name="Station 1",
            address="",
            city="",
            state="IL",
            latitude=41.8,
            longitude=-87.6,
            price_per_gallon=Decimal("3.00"),
        )
        FuelStation.objects.create(
            station_id=2,
            name="Station 2",
            address="",
            city="",
            state="NE",
            latitude=41.0,
            longitude=-96.0,
            price_per_gallon=Decimal("3.20"),
        )
        FuelStation.objects.create(
            station_id=3,
            name="Station 3",
            address="",
            city="",
            state="CO",
            latitude=39.7,
            longitude=-104.9,
            price_per_gallon=Decimal("3.50"),
        )

        # Reset spatial index singleton and initialize it
        from repositories.fuel_station_repository import FuelStationRepository
        self.repo = FuelStationRepository()
        self.spatial_service = SpatialIndexService(repository=self.repo)
        self.spatial_service.refresh_index()

    @responses.activate
    def test_optimize_trip_success(self):
        # Mock ORS Geocoding
        responses.add(
            responses.GET,
            "https://api.openrouteservice.org/geocode/search",
            json={"features": [{"geometry": {"coordinates": [-87.6, 41.8]}}]},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://api.openrouteservice.org/geocode/search",
            json={"features": [{"geometry": {"coordinates": [-104.9, 39.7]}}]},
            status=200,
        )
        # Mock ORS Directions
        responses.add(
            responses.GET,
            "https://api.openrouteservice.org/v2/directions/driving-car",
            json={
                "features": [
                    {
                        "geometry": {
                            "coordinates": [
                                [-87.6, 41.8],  # Chicago
                                [-96.0, 41.0],  # Middle (Nebraska)
                                [-104.9, 39.7],  # Denver
                            ]
                        },
                        "properties": {
                            "segments": [{"distance": 1600000, "duration": 54000}]
                        },
                    }
                ]
            },
            status=200,
        )

        url = reverse("trip-optimize")
        data = {
            "origin": "Chicago, IL",
            "destination": "Denver, CO",
            "max_range_miles": 500.0,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("route_metadata", response.data)
        self.assertIn("fuel_stops", response.data)
        self.assertIn("total_fuel_cost", response.data)
        self.assertGreater(len(response.data["fuel_stops"]), 0)

    def test_invalid_request(self):
        url = reverse("trip-optimize")
        # Missing destination
        data = {"origin": "Chicago, IL"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
