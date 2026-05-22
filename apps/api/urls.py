from django.urls import path

from apps.api.auth_views import AlloRouteTokenObtainPairView, AlloRouteTokenRefreshView
from apps.api.views import TripOptimizeView

urlpatterns = [
    # Authentication
    path("auth/login/", AlloRouteTokenObtainPairView.as_view(), name="auth-login"),
    path("auth/refresh/", AlloRouteTokenRefreshView.as_view(), name="auth-refresh"),
    
    # Trips
    path("trips/optimize/", TripOptimizeView.as_view(), name="trip-optimize"),
]
