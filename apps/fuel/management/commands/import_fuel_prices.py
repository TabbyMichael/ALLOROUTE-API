import csv
import logging
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.fuel.models import FuelStation

logger = logging.getLogger("apps.fuel")

class Command(BaseCommand):
    help = "Ingest fuel station data from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the fuel prices CSV file.")
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Number of records to insert per batch.",
        )
        parser.add_argument(
            "--clear-existing",
            action="store_true",
            help="Clear all existing stations before importing.",
        )

    def handle(self, *args, **options):
        csv_file_path = options["csv_file"]
        batch_size = options["batch_size"]
        clear_existing = options["clear_existing"]

        if clear_existing:
            self.stdout.write(self.style.WARNING("Clearing existing stations..."))
            FuelStation.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(f"Starting ingestion from {csv_file_path}..."))

        try:
            with open(csv_file_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                
                # Column mapping based on expected format
                # Adjust these if the CSV headers differ
                column_map = {
                    "station_id": "OPIS Truckstop ID",
                    "name": "Truckstop Name",
                    "address": "Address",
                    "city": "City",
                    "state": "State",
                    "latitude": "Latitude",
                    "longitude": "Longitude",
                    "price": "Retail Price",
                }

                stations_to_create = []
                total_processed = 0
                total_saved = 0
                errors = 0

                for row in reader:
                    total_processed += 1
                    try:
                        station_data = self._parse_row(row, column_map)
                        if station_data:
                            stations_to_create.append(FuelStation(**station_data))
                        else:
                            errors += 1
                    except Exception as e:
                        logger.error(f"Error parsing row {total_processed}: {e}")
                        errors += 1

                    if len(stations_to_create) >= batch_size:
                        saved = self._bulk_save(stations_to_create)
                        total_saved += saved
                        stations_to_create = []
                        self.stdout.write(f"Processed {total_processed} rows, saved {total_saved} stations...")

                # Save remaining stations
                if stations_to_create:
                    saved = self._bulk_save(stations_to_create)
                    total_saved += saved

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Ingestion complete. Processed: {total_processed}, Saved: {total_saved}, Errors/Skipped: {errors}"
                    )
                )

        except FileNotFoundError:
            raise CommandError(f"File {csv_file_path} not found.")
        except Exception as e:
            raise CommandError(f"An error occurred during ingestion: {e}")

    def _parse_row(self, row: Dict, mapping: Dict) -> Optional[Dict]:
        """
        Validates and cleans a single CSV row.
        Returns a dict for FuelStation or None if invalid.
        """
        try:
            # Required fields and basic validation
            raw_id = row.get(mapping["station_id"])
            if not raw_id:
                return None
            
            station_id = int(raw_id)
            
            # Geographic coordinates validation
            lat_str = row.get(mapping["latitude"])
            lng_str = row.get(mapping["longitude"])
            if not lat_str or not lng_str:
                return None
            
            latitude = float(lat_str)
            longitude = float(lng_str)
            
            # Pricing validation
            price_str = row.get(mapping["price"])
            if not price_str:
                return None
            
            price_per_gallon = Decimal(price_str)

            return {
                "station_id": station_id,
                "name": row.get(mapping["name"], "Unknown"),
                "address": row.get(mapping["address"], ""),
                "city": row.get(mapping["city"], ""),
                "state": row.get(mapping["state"], ""),
                "latitude": latitude,
                "longitude": longitude,
                "price_per_gallon": price_per_gallon,
            }
        except (ValueError, InvalidOperation, TypeError) as e:
            logger.debug(f"Row validation failed: {e}")
            return None

    def _bulk_save(self, stations: List[FuelStation]) -> int:
        """
        Performs a bulk upsert operation.
        Updates existing records if station_id matches.
        """
        try:
            with transaction.atomic():
                FuelStation.objects.bulk_create(
                    stations,
                    unique_fields=["station_id"],
                    update_fields=[
                        "name", "address", "city", "state", 
                        "latitude", "longitude", "price_per_gallon"
                    ],
                )
            return len(stations)
        except Exception as e:
            logger.error(f"Bulk save failed: {e}")
            return 0
