import hashlib
import json
import logging
from typing import Any, Optional

from django.core.cache import cache

logger = logging.getLogger("infrastructure.performance")


class CacheService:
    """
    Utility service for managing application-level caching.
    Uses Django's cache framework (configured for Redis in production).
    """

    @staticmethod
    def _generate_key(prefix: str, data: Any) -> str:
        """Generates a stable cache key based on input data."""
        serialized_data = json.dumps(data, sort_keys=True)
        hash_val = hashlib.md5(serialized_data.encode()).hexdigest()
        return f"{prefix}:{hash_val}"

    def get_cached_route(self, origin: str, destination: str) -> Optional[Any]:
        key = self._generate_key("route", {"o": origin, "d": destination})
        result = cache.get(key)
        if result:
            logger.info(
                f"Cache HIT for route: {origin} -> {destination}",
                extra={"cache_type": "route", "hit": True},
            )
        else:
            logger.debug(
                f"Cache MISS for route: {origin} -> {destination}",
                extra={"cache_type": "route", "hit": False},
            )
        return result

    def set_cached_route(
        self, origin: str, destination: str, route_data: Any, timeout: int = 3600
    ):
        key = self._generate_key("route", {"o": origin, "d": destination})
        cache.set(key, route_data, timeout)
        logger.debug(f"Cache SET for route: {origin} -> {destination}")

    def get_cached_optimization(
        self, origin: str, destination: str, vehicle_params: dict
    ) -> Optional[Any]:
        key = self._generate_key(
            "opt", {"o": origin, "d": destination, "v": vehicle_params}
        )
        result = cache.get(key)
        if result:
            logger.info(
                f"Cache HIT for optimization: {origin} -> {destination}",
                extra={"cache_type": "opt", "hit": True},
            )
        else:
            logger.debug(
                f"Cache MISS for optimization: {origin} -> {destination}",
                extra={"cache_type": "opt", "hit": False},
            )
        return result

    def set_cached_optimization(
        self,
        origin: str,
        destination: str,
        vehicle_params: dict,
        result: Any,
        timeout: int = 1800,
    ):
        key = self._generate_key(
            "opt", {"o": origin, "d": destination, "v": vehicle_params}
        )
        cache.set(key, result, timeout)
        logger.debug(f"Cache SET for optimization: {origin} -> {destination}")
