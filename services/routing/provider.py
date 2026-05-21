from typing import Protocol, runtime_checkable, Optional, Dict, Any
from apps.trips.domain import RouteMetadata, Coordinate
from apps.common.exceptions import (
    AlloRouteError, 
    ResourceNotFoundError, 
    ExternalServiceError,
    ServiceTimeoutError
)

@runtime_checkable
class RoutingProvider(Protocol):
    """
    Interface for routing providers.
    Ensures that any provider (ORS, Google Maps, Mapbox) follows the same contract.
    """
    def get_route(self, origin: str, destination: str) -> RouteMetadata:
        """
        Fetches route details between origin and destination.
        
        Args:
            origin: Starting location string (e.g., "Chicago, IL")
            destination: Ending location string (e.g., "Los Angeles, CA")
            
        Returns:
            RouteMetadata containing polyline, distance, and duration.
            
        Raises:
            RoutingError: If the route cannot be calculated or provider is unavailable.
        """
        ...

class RoutingError(AlloRouteError):
    """Base exception for routing related errors."""
    pass

class RouteNotFoundError(ResourceNotFoundError, RoutingError):
    """Raised when no route is found between points."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="route_not_found", details=details)

class ProviderUnavailableError(ExternalServiceError, RoutingError):
    """Raised when the external API is unreachable or returns a server error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="provider_unavailable", details=details)

class ProviderTimeoutError(ServiceTimeoutError, RoutingError):
    """Raised when the routing provider request times out."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="provider_timeout", details=details)

class ProviderRateLimitError(ExternalServiceError, RoutingError):
    """Raised when the routing provider returns a 429 Too Many Requests."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="provider_rate_limit", details=details)
