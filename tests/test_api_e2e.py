from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.trips.domain import OptimizationResult, RouteMetadata, VehicleConfig


@pytest.mark.django_db
class TestTripAPI:
    """
    End-to-end API tests.
    Validates request validation, response structure, and error handling.
    """

    @pytest.fixture
    def api_client(self):
        return APIClient()

    def test_optimize_trip_success(self, api_client):
        """Test successful optimization request."""
        url = reverse("trip-optimize")
        payload = {"origin": "Chicago, IL", "destination": "Los Angeles, CA"}

        # We need to patch the instance on the view or the class itself before instantiation
        from apps.trips.domain import Coordinate, FuelStationDTO, FuelStop
        from services.trips.trip_planner import TripPlannerService

        mock_result = OptimizationResult(
            route_metadata=RouteMetadata("A", "B", 1000.0, 40000, "poly"),
            fuel_stops=[
                FuelStop(
                    station=FuelStationDTO(
                        1, "S1", "Addr", "City", "ST", Coordinate(0, 0), 3.0
                    ),
                    gallons_to_buy=10.0,
                    cost=30.0,
                    distance_from_start=100.0,
                    remaining_range_after_refuel=500.0,
                )
            ],
            total_fuel_cost=150.0,
            total_gallons=45.0,
            vehicle_config=VehicleConfig(),
        )

        with patch(
            "apps.api.views.TripPlannerService.plan_optimized_trip",
            return_value=mock_result,
        ):
            response = api_client.post(url, payload, format="json")

        assert response.status_code == 200
        assert "trip" in response.data or "route_metadata" in response.data

    def test_invalid_request_payload(self, api_client):
        """Test validation error for missing fields."""
        url = reverse("trip-optimize")
        payload = {"origin": "Chicago"}  # Missing destination

        response = api_client.post(url, payload, format="json")

        assert response.status_code == 400
        assert "error" in response.data

    def test_service_failure_handling(self, api_client):
        """Test how the API handles downstream service errors."""
        url = reverse("trip-optimize")
        payload = {"origin": "Chicago, IL", "destination": "Los Angeles, CA"}

        from apps.common.exceptions import ExternalServiceError

        with patch(
            "apps.api.views.TripPlannerService.plan_optimized_trip",
            side_effect=ExternalServiceError("ORS is down"),
        ):
            response = api_client.post(url, payload, format="json")

        assert (
            response.status_code == 400
        )  # Our custom handler maps this to 400 by default if not mapped
        assert response.data["error"]["code"] == "external_service_error"
