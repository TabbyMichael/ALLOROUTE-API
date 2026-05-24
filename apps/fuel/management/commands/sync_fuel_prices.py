import json
import logging
from decimal import Decimal

import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError

from apps.fuel.models import FuelStation

logger = logging.getLogger(__name__)

# Simple coordinate lookup for major cities to make the prototype map look real
CITY_COORDINATES = {
    "NY": {
        "New York": (40.7128, -74.0060),
        "Albany": (42.6526, -73.7562),
        "Buffalo": (42.8864, -78.8784),
        "Syracuse": (43.0481, -76.1474),
        "Rochester": (43.1566, -77.6088),
        "Binghamton": (42.0987, -75.9125),
        "Poughkeepsie": (41.7004, -73.9210),
        "Yonkers": (40.9312, -73.8987),
        "Utica": (43.1009, -75.2327),
        "White Plains": (41.0340, -73.7629),
    },
    "CA": {
        "Los Angeles": (34.0522, -118.2437),
        "San Francisco": (37.7749, -122.4194),
        "San Diego": (32.7157, -117.1611),
        "Sacramento": (38.5816, -121.4944),
    }
}

class Command(BaseCommand):
    help = "Syncs fuel prices from CollectAPI for a given state"

    def add_arguments(self, parser):
        parser.add_argument(
            "--state",
            type=str,
            default="NY",
            help="Two-letter state code (e.g., NY, CA, TX)",
        )

    def handle(self, *args, **options):
        state = options["state"].upper()
        api_key = settings.COLLECT_API_KEY

        if not api_key:
            raise CommandError(
                "COLLECT_API_KEY not found in settings. Please add it to your .env file."
            )

        url = f"https://api.collectapi.com/gasPrice/stateUsaPrice?state={state}"
        headers = {
            "content-type": "application/json",
            "authorization": f"apikey {api_key}",
        }

        self.stdout.write(f"Fetching gas prices for state: {state}...")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise CommandError(f"API Error: {data.get('message', 'Unknown error')}")

            result = data.get("result", {})
            state_data = result.get("state", {})
            cities = result.get("cities", [])

            if not cities:
                self.stdout.write(self.style.WARNING(f"No city-level data found for {state}. Using state average for primary locations."))
                cities = [
                    {"name": "Capital City", "gasoline": state_data.get("gasoline", "3.50")},
                ]

            count = 0
            for city_info in cities:
                full_city_name = city_info.get("name", "Unknown")
                # Strip suffixes like "-Schenectady-Troy" to match our lookup table
                city_key = full_city_name.split('-')[0].split('/')[0].strip()
                price = city_info.get("gasoline", "3.50")
                
                station_id_hash = hash(f"{state}-{full_city_name}") % 1000000
                
                # Get real coordinates if we have them, otherwise fallback to NYC or State Center
                coords = CITY_COORDINATES.get(state, {}).get(city_key)
                if coords:
                    lat, lng = coords
                else:
                    # Fallback to a random offset from NYC to at least not stack them
                    lat = 40.7128 + (hash(city_key) % 100) / 500.0
                    lng = -74.0060 + (hash(city_key + "alt") % 100) / 500.0
                
                FuelStation.objects.update_or_create(
                    station_id=station_id_hash,
                    defaults={
                        "name": f"Station {full_city_name}",
                        "address": f"Central {full_city_name}",
                        "city": full_city_name,
                        "state": state,
                        "location": Point(lng, lat),
                        "price_per_gallon": Decimal(str(price)),
                    },
                )
                count += 1

            self.stdout.write(
                self.style.SUCCESS(f"Successfully synced {count} entries for {state} with improved locations.")
            )

        except requests.exceptions.RequestException as e:
            raise CommandError(f"Network error: {str(e)}")
        except Exception as e:
            raise CommandError(f"Unexpected error: {str(e)}")
