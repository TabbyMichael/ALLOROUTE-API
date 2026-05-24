# AlloRoute: Algorithmic Fuel Optimization API

AlloRoute is a high-performance REST API built with Django 5.x, designed to solve the "Cheapest Path with Fuel Constraints" problem. It calculates optimal driving routes across the USA, identifying the most cost-effective fuel stops while strictly adhering to vehicle range and efficiency constraints.

## 🚀 Key Features

- **Optimal Fuel Routing**: Identifies the cheapest fuel stations along a route using a greedy look-ahead algorithm.
- **Spatial Precision**: Powered by **PostGIS** for geography-aware spatial queries (`ST_DWithin`).
- **High Performance**: 
    - **Sub-10ms** response times for cached routes.
    - **60% smaller** Docker images (~150MB) for rapid deployment.
- **Resilient Architecture**: Integrated Circuit Breakers (`pybreaker`) and automatic retries for external routing providers.
- **Visual Mapping**: Built-in Leaflet-based frontend for real-time route visualization.

---

## 🛠️ Technical Stack

- **Backend**: Django 5.0, Django REST Framework (DRF)
- **Database**: PostgreSQL 16 + **PostGIS** 3.4
- **Cache**: Redis 7.x (Multi-layer caching for routes and optimization logic)
- **Routing**: OpenRouteService (ORS) Integration
- **Observability**: Structured JSON Logging, Correlation IDs, and OpenTelemetry instrumentation.

---

## 🏃 Getting Started

### Prerequisites
- Docker & Docker Compose **(Recommended)**
- Python 3.12 (for local development)
- OpenRouteService API Key ([Register for free](https://openrouteservice.org/dev/#/signup))

---

### Option A: Running with Docker (Recommended)

This is the fastest way to get the full production-ready stack running.

1. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```env
   DEBUG=False
   SECRET_KEY=production-secret-key
   ORS_API_KEY=your_api_key_here
   DATABASE_URL=postgis://postgres:postgres@db:5432/alloroute
   REDIS_URL=redis://redis:6379/0
   ```

2. **Launch Services**:
   ```bash
   docker compose up -d --build
   ```

3. **Initialize Database**:
   ```bash
   docker compose exec api python manage.py migrate
   docker compose exec api python manage.py import_fuel_prices data/fuel_prices.csv
   ```

### 🔗 Quick Access Links (Localhost)

Once the containers are up and running, you can access the following services:

| Service | Link | Description |
| :--- | :--- | :--- |
| **Trip Dashboard** | [http://localhost:8080/](http://localhost:8080/) | Main interactive map for route visualization. |
| **Swagger Docs** | [http://localhost:8080/api/docs/](http://localhost:8080/api/docs/) | Interactive API documentation and testing. |
| **Redoc Docs** | [http://localhost:8080/api/redoc/](http://localhost:8080/api/redoc/) | Alternative API documentation view. |
| **Health Check** | [http://localhost:8080/health/](http://localhost:8080/health/) | Verify system status. |
| **Django Admin** | [http://localhost:8080/admin/](http://localhost:8080/admin/) | Backend management interface. |

4. **Access**:
   - **API**: `http://localhost:8080/api/v1/`
   - **Map UI**: `http://localhost:8080/`
   - **Docs (OpenAPI)**: `http://localhost:8080/api/schema/swagger-ui/`

---

### Option B: Local Python Development

1. **Install System Dependencies**:
   Ensure you have PostGIS and GDAL installed on your OS:
   - **Ubuntu/Debian**: `sudo apt-get install postgis gdal-bin libgdal-dev`
   - **macOS**: `brew install postgis gdal`

2. **Setup Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements/dev.txt
   ```

3. **Run Services**:
   Ensure a local PostgreSQL (with PostGIS) and Redis are running, then:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

---

## 📡 API Documentation

### Optimize Trip
`POST /api/v1/trips/optimize/`

**Request Body**:
```json
{
  "origin": "New York, NY",
  "destination": "Los Angeles, CA",
  "max_range_miles": 500.0,
  "miles_per_gallon": 10.0
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8080/api/v1/trips/optimize/ \
     -H "Content-Type: application/json" \
     -d '{"origin": "Miami, FL", "destination": "Seattle, WA"}'
```

---

## 🧪 Testing

The project maintains high coverage with unit and integration tests.

```bash
# Via Docker
docker compose exec api pytest

# Local
pytest --cov=.
```

---

## 📈 Performance & Scalability

By migrating from an in-memory Python `KDTree` to **PostGIS**, the system now scales horizontally without RAM bottlenecks. The spatial lookups for 100k+ stations now consume zero application memory and leverage native database indexing for $O(\log N)$ performance.
