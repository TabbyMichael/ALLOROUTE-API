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
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        
        try:
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
                return Response(
                    {"error": "No valid fuel path found. The destination may be unreachable with current fuel station coverage."},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )

            response_serializer = TripOptimizationResponseSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except RoutingError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Unexpected error during trip optimization")
            return Response(
                {"error": "An internal server error occurred while planning your trip."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
