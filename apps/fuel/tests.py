import os
import csv
from decimal import Decimal
from django.core.management import call_command
from django.test import TestCase
from apps.fuel.models import FuelStation

class IngestFuelPricesTest(TestCase):
    def setUp(self):
        self.csv_file = "test_fuel_prices.csv"
        with open(self.csv_file, mode="w", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "OPIS Truckstop ID", "Truckstop Name", "Address", "City", "State", 
                "Rack ID", "Retail Price", "Latitude", "Longitude"
            ])
            writer.writerow([
                "10", "Valid Station", "Address 1", "City 1", "ST", "100", "3.50", "40.0", "-70.0"
            ])
            writer.writerow([
                "11", "Invalid Price", "Address 2", "City 2", "ST", "101", "not-a-number", "41.0", "-71.0"
            ])
            writer.writerow([
                "12", "Missing Coords", "Address 3", "City 3", "ST", "102", "3.60", "", ""
            ])
            writer.writerow([
                "10", "Duplicate ID", "Address 4", "City 4", "ST", "104", "3.70", "42.0", "-72.0"
            ])

    def tearDown(self):
        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)

    def test_ingestion_valid_and_invalid_data(self):
        """
        Test that valid data is ingested and invalid data is skipped.
        Also test that duplicate IDs are handled (ignored due to ignore_conflicts).
        """
        call_command("import_fuel_prices", self.csv_file)
        
        # Only the first row should be saved. 
        # Row 2 has invalid price.
        # Row 3 has missing coords.
        # Row 4 is duplicate ID.
        self.assertEqual(FuelStation.objects.count(), 1)
        
        station = FuelStation.objects.get(station_id=10)
        self.assertEqual(station.name, "Valid Station")
        self.assertEqual(station.price_per_gallon, Decimal("3.50"))
        self.assertEqual(station.latitude, 40.0)

    def test_ingestion_file_not_found(self):
        """Test that CommandError is raised if file does not exist."""
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command("import_fuel_prices", "non_existent.csv")
