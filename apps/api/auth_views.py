from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .auth_serializers import AlloRouteTokenObtainPairSerializer
from .exceptions import custom_exception_handler


class AlloRouteTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that returns access and refresh tokens.
    """
    serializer_class = AlloRouteTokenObtainPairSerializer
    def get_exception_handler(self):
        return custom_exception_handler

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Token pair generated successfully"),
            401: OpenApiResponse(description="Invalid credentials")
        },
        tags=["Authentication"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AlloRouteTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view.
    """
    def get_exception_handler(self):
        return custom_exception_handler

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Token refreshed successfully"),
            401: OpenApiResponse(description="Invalid or expired refresh token")
        },
        tags=["Authentication"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
