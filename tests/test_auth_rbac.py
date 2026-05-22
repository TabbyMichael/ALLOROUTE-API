import pytest
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from apps.common.roles import UserRole

@pytest.mark.django_db
class TestRBACIntegration:
    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("trip-optimize")

        # Setup users
        self.basic_user = User.objects.create_user(username="basic", password="password")
        self.basic_user.profile.role = UserRole.BASIC.value
        self.basic_user.profile.save()

        self.premium_user = User.objects.create_user(username="premium", password="password")
        self.premium_user.profile.role = UserRole.PREMIUM.value
        self.premium_user.profile.save()

    def test_basic_user_limit_enforcement(self):
        # Authenticate as basic
        self.client.force_authenticate(user=self.basic_user)

        with patch("services.trips.trip_planner.TripPlannerService.plan_optimized_trip") as mock_plan:
            from apps.common.exceptions import ValidationError
            mock_plan.side_effect = ValidationError("Basic tier limit exceeded", code="tier_limit_exceeded")

            # Need valid origin/destination (>= 2 chars)
            response = self.client.post(self.url, {"origin": "Chicago, IL", "destination": "Los Angeles, CA", "max_range_miles": 500, "miles_per_gallon": 10}, format="json")

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            # DRF ValidationError adds the code to details
            assert response.data["error"]["code"] == "tier_limit_exceeded"

    def test_premium_user_access(self):
        self.client.force_authenticate(user=self.premium_user)

        with patch("services.trips.trip_planner.TripPlannerService.plan_optimized_trip") as mock_plan:
            # Mock successful plan
            from apps.trips.domain import OptimizationResult, RouteMetadata, VehicleConfig
            mock_plan.return_value = OptimizationResult(
                route_metadata=RouteMetadata("A", "B", 500, 3600, "polyline"),
                fuel_stops=[], total_fuel_cost=0, total_gallons=0, execution_ms=0, generated_at=None,
                vehicle_config=VehicleConfig()
            )

            # Ensure authenticated user accesses correctly
            response = self.client.post(self.url, {"origin": "Chicago, IL", "destination": "Los Angeles, CA", "max_range_miles": 500, "miles_per_gallon": 10}, format="json")
            assert response.status_code == status.HTTP_200_OK
