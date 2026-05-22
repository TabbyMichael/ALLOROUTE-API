from django.contrib.gis.db import models
from django.db import models as base_models


class FuelStation(base_models.Model):
    """
    Persistence model for fuel stations ingested from the provided dataset.
    Uses PostGIS PointField for high-performance spatial queries.
    """

    station_id = base_models.IntegerField(
        unique=True, help_text="Original ID from the dataset"
    )
    name = base_models.CharField(max_length=255)
    address = base_models.CharField(max_length=255)
    city = base_models.CharField(max_length=100)
    state = base_models.CharField(max_length=2, help_text="Two-letter state code")

    # Geographic coordinates (PostGIS)
    location = models.PointField(geography=True, help_text="GIS location (lng, lat)")

    # Pricing
    price_per_gallon = base_models.DecimalField(max_digits=10, decimal_places=3)

    # Metadata
    updated_at = base_models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            base_models.Index(fields=["price_per_gallon"]),
            base_models.Index(fields=["state", "city"]),
            base_models.Index(fields=["name"]),
        ]
        verbose_name = "Fuel Station"
        verbose_name_plural = "Fuel Stations"

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state} (${self.price_per_gallon})"
