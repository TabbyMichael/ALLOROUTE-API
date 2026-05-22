from django.db import models


class TripOptimizationRequest(models.Model):
    """
    Optional persistence for optimization requests (audit logging/caching).
    """

    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)

    # Request parameters
    vehicle_range = models.FloatField(default=500.0)
    fuel_efficiency = models.FloatField(default=10.0)

    # Results (can be stored as JSON for historical purposes)
    result_data = models.JSONField(null=True, blank=True)

    # Performance metrics
    execution_time_ms = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.origin} to {self.destination} ({self.created_at})"
