class RoutingProviderError(Exception):
    """Base exception for routing provider errors."""

    pass


class LocationNotFoundError(RoutingProviderError):
    """Raised when a location could not be resolved."""

    pass
