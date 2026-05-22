from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers.trip_serializer import TripRequestSerializer
from services.fuel.downsampler import RouteProcessor
from services.fuel.exceptions import NoFuelAvailableError
from services.fuel.optimizer import FuelOptimizerService
from services.routing.ors_client import OpenRouteServiceProvider


class TripOptimizeView(APIView):
    def post(self, request):
        serializer = TripRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        start = serializer.validated_data["start"]
        finish = serializer.validated_data["finish"]

        # 1. Routing
        provider = OpenRouteServiceProvider(api_key=settings.ORS_API_KEY)
        route_data = provider.fetch_route_geometry(start, finish)

        # 2. Downsampling
        nodes = RouteProcessor.downsample(route_data["coordinates"])

        # 3. Optimization
        optimizer = FuelOptimizerService()
        try:
            stops, cost, gallons = optimizer.optimize(nodes)
        except NoFuelAvailableError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        return Response(
            {
                "trip": {
                    "distance": route_data["distance_miles"],
                    "duration": route_data["duration_hours"],
                },
                "route": {"coordinates": route_data["coordinates"]},
                "fuel_summary": {"total_cost": cost, "total_gallons": gallons},
                "fuel_stops": stops,
            }
        )
