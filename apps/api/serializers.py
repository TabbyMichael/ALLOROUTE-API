from rest_framework import serializers

class TripOptimizationRequestSerializer(serializers.Serializer):
    """
    Serializer for the trip optimization request.
    """
    origin = serializers.CharField(
        help_text="Starting location (e.g., 'New York, NY')",
        required=True
    )
    destination = serializers.CharField(
        help_text="Ending location (e.g., 'Los Angeles, CA')",
        required=True
    )
    
    # Optional vehicle overrides
    max_range_miles = serializers.FloatField(
        default=500.0,
        help_text="Maximum range of the vehicle in miles."
    )
    miles_per_gallon = serializers.FloatField(
        default=10.0,
        help_text="Fuel efficiency of the vehicle."
    )

class FuelStationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    latitude = serializers.FloatField(source="coordinate.latitude")
    longitude = serializers.FloatField(source="coordinate.longitude")
    price_per_gallon = serializers.FloatField()

class FuelStopSerializer(serializers.Serializer):
    station = FuelStationSerializer()
    gallons_to_buy = serializers.FloatField()
    cost = serializers.FloatField()
    distance_from_start = serializers.FloatField()
    remaining_range_after_refuel = serializers.FloatField()

class RouteMetadataSerializer(serializers.Serializer):
    origin = serializers.CharField()
    destination = serializers.CharField()
    total_distance_miles = serializers.FloatField()
    total_duration_seconds = serializers.FloatField()
    polyline = serializers.CharField()

class TripOptimizationResponseSerializer(serializers.Serializer):
    """
    Serializer for the final optimization result.
    """
    route_metadata = RouteMetadataSerializer()
    fuel_stops = FuelStopSerializer(many=True)
    total_fuel_cost = serializers.FloatField()
    total_gallons = serializers.FloatField()
    
    # Performance and metadata
    execution_ms = serializers.FloatField()
    generated_at = serializers.DateTimeField()
