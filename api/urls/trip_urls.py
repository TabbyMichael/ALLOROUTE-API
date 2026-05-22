from django.urls import path

from api.views.trip_views import TripOptimizeView

urlpatterns = [
    path("trips/optimize/", TripOptimizeView.as_view(), name="trip-optimize"),
]
