from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from infrastructure.performance.middleware import PerformanceMetricsMiddleware
from infrastructure.performance.cache_service import CacheService
from django.core.cache import cache

class PerformanceFeaturesTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.cache_service = CacheService()
        cache.clear()

    def test_performance_middleware(self):
        def get_response(request):
            return HttpResponse("OK")
        
        middleware = PerformanceMetricsMiddleware(get_response)
        request = self.factory.get("/")
        response = middleware(request)
        
        self.assertIn("X-Response-Time-Ms", response)
        self.assertEqual(response.status_code, 200)

    def test_cache_service_route(self):
        origin, destination = "NYC", "LA"
        route_data = {"polyline": "abc", "distance": 3000}
        
        # Set cache
        self.cache_service.set_cached_route(origin, destination, route_data)
        
        # Get cache
        cached = self.cache_service.get_cached_route(origin, destination)
        self.assertEqual(cached, route_data)

    def test_cache_service_optimization(self):
        origin, destination = "NYC", "LA"
        vehicle_params = {"range": 500, "mpg": 10}
        result = "OptimizationResult"
        
        self.cache_service.set_cached_optimization(origin, destination, vehicle_params, result)
        
        cached = self.cache_service.get_cached_optimization(origin, destination, vehicle_params)
        self.assertEqual(cached, result)
