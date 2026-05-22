# AlloRoute API: Geospatial Fuel Optimization Engine

AlloRoute is an enterprise-grade backend system designed to solve the **Constrained Shortest Path Optimization** problem for long-distance vehicle travel. It calculates the most cost-effective fuel stops along a route in the USA, adhering to vehicle range constraints while minimizing total economic cost.

## 🚀 Architectural Vision

Built with **Django 5** and **Clean Architecture**, AlloRoute is designed as a modular, service-oriented system that prioritizes algorithmic efficiency, operational observability, and scalability.

### Core Design Principles
- **Domain-Driven Design (DDD)**: Business logic is decoupled from framework concerns using typed DTOs and Protocols.
- **Single-Call Routing**: External API dependency is strictly minimized to exactly one route request per trip.
- **Complexity Reduction**: Multi-stage pipeline to reduce search space from 100k+ stations to ~50-100 relevant candidates.
- **Observability First**: Structured JSON logging, correlation IDs, and comprehensive performance instrumentation.

---

## 🧠 The Optimization Pipeline

AlloRoute treats fuel planning as a **Directed Acyclic Graph (DAG)** optimization problem.

### 1. Route Generation & API Minimization
The system calls the **OpenRouteService (ORS)** exactly once to fetch the full polyline geometry. This geometry is then cached in Redis to eliminate redundant external calls for repeated origin-destination pairs.

### 2. Geospatial Candidate Reduction (The "Corridor" Search)
Instead of querying every point on a long route, we implement a two-stage reduction:
- **Spatial Indexing**: An in-memory **KDTree** provides sub-millisecond radius lookups across the entire US fuel station dataset (~100k stations).
- **Segment-Based Filtering**: The route is downsampled into "checkpoints." We query a 10-mile corridor around these points and group results into segments (e.g., every 50 miles), keeping only the N most competitive stations per segment.
- **Result**: Reduces $O(N \times M)$ complexity to $O(\log N)$ spatial lookup followed by $O(K^2)$ graph optimization.

### 3. Graph Optimization Engine (Dynamic Programming)
We model reachable stations as nodes in a DAG.
- **Edge Weight**: The financial cost to travel between two stations, calculated as `(Distance / MPG) * Price_at_Source`.
- **Constraint**: An edge only exists if `Distance <= Vehicle_Max_Range`.
- **Pathfinding**: A Dynamic Programming (DP) approach finds the global minimum cost path from start to finish.

### 4. Intelligent Purchasing Strategy
The engine implements realistic economic behavior:
- **Cheaper Fuel Ahead**: If a reachable station ahead has a lower price, the system recommends buying only enough fuel to reach that cheaper station.
- **Aggressive Refuel**: If future fuel is more expensive, the system fills the tank completely.

---

## 🛠️ Technical Stack & Infrastructure

- **Backend**: Django 5.x, Django REST Framework (DRF)
- **Spatial Search**: `scipy.spatial.KDTree` (In-memory for low-latency lookups)
- **Caching**: Redis (Multi-level: Route caching + Optimization result caching)
- **Observability**: `python-json-logger`, Correlation ID middleware, Prometheus-ready metrics.
- **Database**: PostgreSQL (Persistence for fuel station data)
- **Documentation**: OpenAPI 3.0 (drf-spectacular)

---

## 📊 Performance Discussion

| Stage | Strategy | Performance Impact |
| :--- | :--- | :--- |
| **Routing** | Redis Caching | Avoids 1-2s API latency on repeats |
| **Spatial Query** | KDTree | Sub-1ms lookups (vs 50-100ms SQL) |
| **Optimization** | Segment Filtering | Keeps graph nodes $< 100$ for $O(K^2)$ speed |
| **Orchestration** | Service Layers | < 150ms total local processing time |

### Engineering Tradeoffs
- **In-Memory vs. PostGIS**: We selected an in-memory KDTree for lookups. *Tradeoff*: Faster response times and simpler deployment for the assignment, at the cost of higher RAM usage (~200MB). In a distributed production environment, this would migrate to PostGIS.
- **Downsampling**: We downsample route points to roughly every 10 miles. *Tradeoff*: Significant reduction in computational load with negligible loss in fuel station discovery fidelity.

---

## 💻 Setup & Execution

### Prerequisites
- Docker & Docker Compose
- OpenRouteService API Key ([Get one here](https://openrouteservice.org/))

### Quick Start
1. **Clone & Configure**:
   ```bash
   cp .env.example .env
   # Edit .env and add your ORS_API_KEY
   ```

2. **Launch with Docker**:
   ```bash
   docker-compose up --build
   ```

3. **Ingest Data**:
   ```bash
   docker-compose exec api python manage.py import_fuel_prices data/fuel_prices.csv
   ```

### API Usage Example
**POST** `/api/v1/trips/optimize/`
```json
{
  "origin": "Chicago, IL",
  "destination": "Los Angeles, CA",
  "max_range_miles": 500.0,
  "miles_per_gallon": 10.0
}
```

---

## 🔒 Security & Resilience

AlloRoute is built with a "Security by Design" mindset, incorporating multiple layers of protection:

### 1. API Abuse Prevention
- **Rate Limiting**: Implemented using Django REST Framework's `AnonRateThrottle` and `UserRateThrottle` to protect external API quotas and prevent DoS attacks.
- **Strict Validation**: All incoming requests are validated for length, format, and character set using regex and range validators.
- **Payload Limits**: Enforced strict `DATA_UPLOAD_MAX_MEMORY_SIZE` to prevent oversized request abuse.

### 2. Infrastructure Hardening
- **Secure Headers**: Configured HSTS, X-Content-Type-Options, and X-Frame-Options via Django's `SecurityMiddleware`.
- **CORS Policy**: Strictly controlled `CORS_ALLOWED_ORIGINS` in production; wildcards are disabled.
- **Non-Root Execution**: Docker containers run as a non-privileged `django` user.

### 3. Operational Security
- **Log Sanitization**: Automated middleware to scrub sensitive query parameters (e.g., API keys) from all structured logs.
- **Sanitized Errors**: Custom exception handler ensures internal stack traces and provider-specific details are never exposed to the client.
- **Safe Timeouts**: All external API requests use strict timeouts and limited retry policies to prevent resource exhaustion.

---

## 🧪 Testing & Quality Assurance

The system maintains a **multi-layered testing strategy**:
- **Unit Tests**: Pure logic tests for the DP optimizer and geometry utilities.
- **Integration Tests**: Full pipeline validation with mocked external APIs.
- **E2E API Tests**: Standardized request/response validation.
- **Performance Benchmarks**: Automated tests to ensure sub-200ms processing thresholds.

Run tests:
```bash
docker-compose exec api pytest
```

---

## 📈 Future Improvements
1. **Real-time Traffic**: Integrate traffic-aware duration estimates from ORS.
2. **PostGIS Migration**: Shift spatial indexing to the database for horizontally scaled deployments.
3. **Multi-Vehicle Support**: Add DTOs for electric vehicle (EV) charging curves.
4. **detour Heuristics**: Factor in the time-cost of detouring off the main highway.

---

**Developed with 🛠️ by Kibugu Ian for the AlloRoute Engineering Challenge.**
