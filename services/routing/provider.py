from typing import Protocol, runtime_checkable
from apps.trips.domain import RouteMetadata, Coordinate

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

class RoutingError(Exception):
    """Base exception for routing related errors."""
    pass

class RouteNotFoundError(RoutingError):
    """Raised when no route is found between points."""
    pass

class ProviderUnavailableError(RoutingError):
    """Raised when the external API is unreachable or returns a server error."""
    pass
