from django.db import models

class FuelStation(models.Model):
    """
    Persistence model for fuel stations ingested from the provided dataset.
    """
    station_id = models.IntegerField(unique=True, help_text="Original ID from the dataset")
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2, help_text="Two-letter state code")
    
    # Geographic coordinates
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    # Pricing
    price_per_gallon = models.DecimalField(max_digits=10, decimal_places=3)
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["price_per_gallon"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state} (${self.price_per_gallon})"
