from celery import shared_task
from apps.trips.domain import VehicleConfig
from services.trips.trip_planner import TripPlannerService
from apps.api.serializers import TripOptimizationRequestSerializer

@shared_task(bind=True)
def plan_trip_task(self, data, user_id=None):
    # This is a bit simplified, ideally we pass the full user object or id
    # TripPlannerService.plan_optimized_trip needs to handle user-id to profile resolution
    planner = TripPlannerService()
    vehicle_config = VehicleConfig(
        max_range_miles=data.get("max_range_miles", 500.0),
        miles_per_gallon=data.get("miles_per_gallon", 10.0),
    )
    
    # We pass user_id instead of user object because user objects are not serializable
    # Need to update TripPlannerService/View logic later to handle this.
    return planner.plan_optimized_trip(
        origin=data["origin"],
        destination=data["destination"],
        vehicle_config=vehicle_config,
        user=user_id,
    )
