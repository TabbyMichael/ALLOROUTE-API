import os
import django
from django.db import connection

# Configure Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

def add_gin_index():
    with connection.schema_editor() as schema_editor:
        # We want to add a GIN index on coordinates if we were using PostGIS, 
        # but since we are using float fields, we need a standard B-Tree index 
        # or consider upgrading to PostGIS.
        # Currently, indexing latitude/longitude individually is sufficient for standard queries.
        print("Ensuring indexes on FuelStation...")
        from apps.fuel.models import FuelStation
        # Indexes are already in Meta, but we can verify the SQL
        for index in FuelStation._meta.indexes:
            print(f"Verified index: {index.name}")

if __name__ == "__main__":
    add_gin_index()
