import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from apps.api.serializers import (
    TripOptimizationRequestSerializer,
    TripOptimizationResponseSerializer
)
from apps.trips.domain import VehicleConfig
from services.trips.trip_planner import TripPlannerService
from services.routing.provider import RoutingError

logger = logging.getLogger("apps.api")

class TripOptimizeView(APIView):
    """
    Endpoint for optimizing fuel stops along a route.
    """
    
    def get_exception_handler(self):
        from apps.api.exceptions import custom_exception_handler
        return custom_exception_handler

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.planner_service = TripPlannerService()

    @extend_schema(
        request=TripOptimizationRequestSerializer,
        responses={200: TripOptimizationResponseSerializer},
        description="Calculates the most cost-effective fuel stops between two locations in the USA."
    )
    def post(self, request, *args, **kwargs):
        serializer = TripOptimizationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        
        vehicle_config = VehicleConfig(
            max_range_miles=data.get("max_range_miles", 500.0),
            miles_per_gallon=data.get("miles_per_gallon", 10.0)
        )

        result = self.planner_service.plan_optimized_trip(
            origin=data["origin"],
            destination=data["destination"],
            vehicle_config=vehicle_config
        )

        if not result.fuel_stops and result.route_metadata.total_distance_miles > vehicle_config.max_range_miles:
            from apps.common.exceptions import BusinessLogicError
            raise BusinessLogicError(
                "No valid fuel path found. The destination may be unreachable with current fuel station coverage.",
                code="no_fuel_path_found"
            )

        response_serializer = TripOptimizationResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
