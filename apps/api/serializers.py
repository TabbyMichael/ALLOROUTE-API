from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from rest_framework import serializers

class TripOptimizationRequestSerializer(serializers.Serializer):
    """
    Serializer for the trip optimization request.
    Includes strict validation to prevent abuse and malformed input.
    """
    origin = serializers.CharField(
        help_text="Starting location (e.g., 'New York, NY')",
        required=True,
        max_length=255,
        min_length=2,
        validators=[RegexValidator(r'^[a-zA-Z0-9\s,.-]+$', "Invalid characters in origin")]
    )
    destination = serializers.CharField(
        help_text="Ending location (e.g., 'Los Angeles, CA')",
        required=True,
        max_length=255,
        min_length=2,
        validators=[RegexValidator(r'^[a-zA-Z0-9\s,.-]+$', "Invalid characters in destination")]
    )
    
    # Optional vehicle overrides with strict ranges
    max_range_miles = serializers.FloatField(
        default=500.0,
        help_text="Maximum range of the vehicle in miles.",
        validators=[MinValueValidator(50.0), MaxValueValidator(2000.0)]
    )
    miles_per_gallon = serializers.FloatField(
        default=10.0,
        help_text="Fuel efficiency of the vehicle.",
        validators=[MinValueValidator(1.0), MaxValueValidator(100.0)]
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
