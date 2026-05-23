import csv
from decimal import Decimal, InvalidOperation

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError

from apps.fuel.models import FuelStation


class Command(BaseCommand):
    help = "Imports fuel station data from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    def handle(self, *args, **options):
        file_path = options["file_path"]
        count = 0
        try:
            with open(file_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # Map CSV headers to model fields
                        # Expected headers: OPIS Truckstop ID, Truckstop Name, Address, City, State, Rack ID, Retail Price, Latitude, Longitude
                        station_id = int(row["OPIS Truckstop ID"])
                        lat = float(row["Latitude"])
                        lng = float(row["Longitude"])
                        
                        _, created = FuelStation.objects.update_or_create(
                            station_id=station_id,
                            defaults={
                                "name": row["Truckstop Name"],
                                "address": row["Address"],
                                "city": row["City"],
                                "state": row["State"],
                                "location": Point(lng, lat),
                                "price_per_gallon": Decimal(row["Retail Price"]),
                            },
                        )
                        if created:
                            count += 1
                    except (ValueError, KeyError, TypeError, InvalidOperation):
                        # Skip invalid rows
                        continue
        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}")

        self.stdout.write(
            self.style.SUCCESS(f"Successfully imported {count} stations.")
        )
