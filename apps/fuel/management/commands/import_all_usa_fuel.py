import time
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = "Syncs fuel prices for all 50 US states from CollectAPI with a delay"

    def handle(self, *args, **options):
        states = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        ]

        self.stdout.write(f"Syncing fuel stations for {len(states)} states...")

        for state in states:
            self.stdout.write(f"Syncing {state}...")
            try:
                call_command("sync_fuel_prices", state=state)
                # Adding a 5-second delay to be polite to the API rate limiter
                time.sleep(5)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to sync {state}: {e}"))
                # If we hit a rate limit, break early
                if "429" in str(e):
                    self.stdout.write(self.style.ERROR("Rate limit hit. Stopping bulk sync."))
                    break

        self.stdout.write(self.style.SUCCESS("Bulk sync process finished."))
