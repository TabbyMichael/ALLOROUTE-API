from django.apps import AppConfig


class FuelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.fuel"

    def ready(self):
        from services.fuel.spatial_index import SpatialIndexService

        try:
            SpatialIndexService.build()
        except Exception:
            # Avoid breaking migrations or other management commands
            pass
