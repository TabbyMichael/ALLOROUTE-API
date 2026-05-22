from unittest.mock import MagicMock, patch

import responses
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.trips.domain import OptimizationResult, RouteMetadata, VehicleConfig


class ObservabilityTest(APITestCase):
    def test_correlation_id_in_response(self):
        """Verify that X-Correlation-ID is returned in the response headers."""
        url = reverse("trip-optimize")
        with patch("apps.api.views.TripPlannerService.plan_optimized_trip") as mock_p:
            mock_p.return_value = OptimizationResult(
                route_metadata=RouteMetadata("A", "B", 100, 100, ""),
                fuel_stops=[],
                total_fuel_cost=0,
                total_gallons=0,
                vehicle_config=VehicleConfig(),
            )
            response = self.client.post(
                url, {"origin": "A", "destination": "B"}, format="json"
            )

        self.assertIn("X-Correlation-ID", response)
        self.assertEqual(len(response["X-Correlation-ID"]), 36)

    def test_custom_correlation_id(self):
        """Verify that the middleware respects an existing X-Correlation-ID header."""
        url = reverse("trip-optimize")
        custom_id = "test-correlation-id-123"
        with patch("apps.api.views.TripPlannerService.plan_optimized_trip") as mock_p:
            mock_p.return_value = OptimizationResult(
                route_metadata=RouteMetadata("A", "B", 100, 100, ""),
                fuel_stops=[],
                total_fuel_cost=0,
                total_gallons=0,
                vehicle_config=VehicleConfig(),
            )
            response = self.client.post(
                url,
                {"origin": "A", "destination": "B"},
                format="json",
                HTTP_X_CORRELATION_ID=custom_id,
            )

        self.assertEqual(response["X-Correlation-ID"], custom_id)

    def test_structured_error_response(self):
        """Verify that errors are returned in the new structured format."""
        url = reverse("trip-optimize")
        # Missing destination will trigger a 400 from DRF validation
        response = self.client.post(url, {"origin": "Chicago"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)
        # In our custom handler, we map DRF errors to our structure
        self.assertEqual(response.data["error"]["code"], 400)

    def test_custom_exception_mapping(self):
        """Verify that AlloRouteError subclasses map to correct status codes."""
        from apps.api.views import TripOptimizeView
        from apps.common.exceptions import (
            ResourceNotFoundError,
            ServiceTimeoutError,
            ServiceUnavailableError,
        )

        url = reverse("trip-optimize")

        test_cases = [
            (ResourceNotFoundError("Station not found"), 404),
            (ServiceTimeoutError("ORS timed out"), 504),
            (ServiceUnavailableError("ORS down"), 503),
        ]

        for exc, expected_status in test_cases:
            with patch(
                "apps.api.views.TripPlannerService.plan_optimized_trip", side_effect=exc
            ):
                response = self.client.post(
                    url, {"origin": "Chicago, IL", "destination": "Los Angeles, CA"}, format="json"
                )
                self.assertEqual(
                    response.status_code, expected_status, f"Failed for {type(exc)}"
                )
                self.assertEqual(response.data["error"]["message"], str(exc))
