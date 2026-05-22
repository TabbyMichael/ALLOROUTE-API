from typing import Any, Dict, Optional


class AlloRouteError(Exception):
    """Base class for all application-specific errors."""

    def __init__(
        self,
        message: str,
        code: str = "internal_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class BusinessLogicError(AlloRouteError):
    """Raised when a business rule is violated."""

    def __init__(
        self,
        message: str,
        code: str = "business_rule_violation",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)


class ValidationError(AlloRouteError):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str,
        code: str = "validation_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)


class ExternalServiceError(AlloRouteError):
    """Raised when an external service (e.g., ORS) fails."""

    def __init__(
        self,
        message: str,
        code: str = "external_service_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)


class ServiceTimeoutError(ExternalServiceError):
    """Raised when an external service request times out."""

    def __init__(
        self,
        message: str,
        code: str = "service_timeout",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)


class ServiceUnavailableError(ExternalServiceError):
    """Raised when an external service is unavailable."""

    def __init__(
        self,
        message: str,
        code: str = "service_unavailable",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)


class ResourceNotFoundError(AlloRouteError):
    """Raised when a requested resource (e.g., route or station) is not found."""

    def __init__(
        self,
        message: str,
        code: str = "resource_not_found",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)


class ConfigurationError(AlloRouteError):
    """Raised when there is a configuration issue (e.g., missing API keys)."""

    def __init__(
        self,
        message: str,
        code: str = "configuration_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)
