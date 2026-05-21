from django.urls import path
from apps.api.views import TripOptimizeView

urlpatterns = [
    path("trips/optimize/", TripOptimizeView.as_view(), name="trip-optimize"),
]
