from django.test import SimpleTestCase
from apps.trips.domain import Coordinate
from services.routing.geometry import GeometryService
import polyline

class GeometryServiceTest(SimpleTestCase):
    def setUp(self):
        self.service = GeometryService()

    def test_decode_polyline(self):
        # Sample polyline for Chicago to Denver area (very simplified)
        points = [(41.8781, -87.6298), (39.7392, -104.9903)]
        encoded = polyline.encode(points)
        
        decoded = self.service.decode_polyline(encoded)
        self.assertEqual(len(decoded), 2)
        self.assertAlmostEqual(decoded[0].latitude, 41.8781, places=4)
        self.assertAlmostEqual(decoded[0].longitude, -87.6298, places=4)

    def test_haversine_distance(self):
        # Distance between Chicago and Denver is roughly 918 miles
        chicago = Coordinate(latitude=41.8781, longitude=-87.6298)
        denver = Coordinate(latitude=39.7392, longitude=-104.9903)
        
        distance = self.service.haversine_distance(chicago, denver)
        self.assertTrue(900 < distance < 950)

    def test_calculate_cumulative_distances(self):
        coords = [
            Coordinate(latitude=0, longitude=0),
            Coordinate(latitude=0, longitude=1),  # ~69 miles
            Coordinate(latitude=0, longitude=2),  # ~69 miles
        ]
        distances = self.service.calculate_cumulative_distances(coords)
        self.assertEqual(len(distances), 3)
        self.assertEqual(distances[0], 0.0)
        self.assertGreater(distances[1], 60.0)
        self.assertGreater(distances[2], 120.0)

    def test_downsample_route(self):
        # Create a "route" with many points
        coords = [Coordinate(latitude=0, longitude=i/10.0) for i in range(101)] # 0 to 10 degrees, ~690 miles
        
        # Downsample every 100 miles
        checkpoints = self.service.downsample_route(coords, interval_miles=100.0)
        
        # Start, ~100, ~200, ~300, ~400, ~500, ~600, End
        # Roughly 8 points
        self.assertLess(len(checkpoints), 15)
        self.assertEqual(checkpoints[0].distance_from_start, 0.0)
        self.assertAlmostEqual(checkpoints[-1].distance_from_start, self.service.calculate_cumulative_distances(coords)[-1])

    def test_get_route_corridor_bounds(self):
        coords = [
            Coordinate(latitude=40.0, longitude=-80.0),
            Coordinate(latitude=42.0, longitude=-82.0),
        ]
        bounds = self.service.get_route_corridor_bounds(coords, buffer_miles=10.0)
        
        min_lat, min_lng, max_lat, max_lng = bounds
        self.assertLess(min_lat, 40.0)
        self.assertGreater(max_lat, 42.0)
        self.assertLess(min_lng, -82.0)
        self.assertGreater(max_lng, -80.0)
