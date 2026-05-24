import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import (
    TripOptimizationRequestSerializer,
    TripOptimizationResponseSerializer,
    ErrorResponseSerializer,
)
from apps.trips.domain import VehicleConfig
from services.trips.trip_planner import TripPlannerService

logger = logging.getLogger("apps.api")


class TripOptimizeView(APIView):
    """
    Endpoint for optimizing fuel stops along a route.
    Available to all users.
    """

    permission_classes = [AllowAny]

    def get_exception_handler(self):
        from apps.api.exceptions import custom_exception_handler
        return custom_exception_handler

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.planner_service = TripPlannerService()

    @extend_schema(
        request=TripOptimizationRequestSerializer,
        responses={
            200: TripOptimizationResponseSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer
        },
        description="Calculates the most cost-effective fuel stops between two locations in the USA.",
        tags=["Trips"]
    )
    def post(self, request, *args, **kwargs):
        serializer = TripOptimizationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        vehicle_config = VehicleConfig(
            max_range_miles=data.get("max_range_miles", 500.0),
            miles_per_gallon=data.get("miles_per_gallon", 10.0),
        )

        result = self.planner_service.plan_optimized_trip(
            origin=data["origin"],
            destination=data["destination"],
            vehicle_config=vehicle_config,
            user=request.user,
        )

        response_serializer = TripOptimizationResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
