# Solution Design — Trips (trips.mulmo.name)

## Architecture

```
User (mobile browser)
  → trips.mulmo.name (Route 53 alias)
  → CloudFront (single distribution)
      ├── /api/*  → Lambda Function URL (Python, eu-north-1)
      └── /*      → S3 frontend bucket (static HTML + CSS)
                        ↕
                    S3 state bucket (private, eu-north-1)
                    Secrets Manager (eu-north-1)
                    SL Journey Planner v2 API
```

## AWS Resources

### CertificateStack (us-east-1)

- ACM certificate for `trips.mulmo.name`
- DNS validation against the existing `mulmo.name` Route 53 hosted zone
- Exports the certificate ARN via `CfnOutput` for cross-stack reference
- Tagged with `Project: TripsApp`

### AppStack (eu-north-1)

- S3 frontend bucket — static assets (HTML + CSS), served via CloudFront with OAC, `DESTROY` on stack delete
- S3 state bucket — private, `BLOCK_ALL` public access, Lambda-only read/write, `RETAIN` on stack delete
- Lambda function (Python 3.12) with function URL enabled
- CloudFront distribution with two behaviors:
  - Default behavior → S3 frontend bucket origin with OAC
  - `/api/*` behavior → Lambda function URL origin with OAC
- Custom domain `trips.mulmo.name` with ACM certificate from CertificateStack
- Route 53 A-record alias: `trips.mulmo.name` → CloudFront distribution
- Imports the existing `mulmo.name` hosted zone via `HostedZone.fromLookup()`
- Secrets Manager secret containing the Trafiklab API key
- IAM permissions: Lambda can read/write state bucket, read the secret
- All resources tagged with `Project: TripsApp`

### Cross-Stack Reference

The CertificateStack exports the ACM certificate ARN. The AppStack imports it using `Fn.importValue()`. Both stacks are instantiated in the same CDK app (`bin/app.ts`), with an explicit dependency so the certificate is created before the distribution.

---

## Persistence — S3 State Document

All user state is stored as a single JSON document (`state.json`) in the private S3 state bucket. The bucket name is passed to Lambda via the `STATE_BUCKET` environment variable.

When no `state.json` exists in S3 (first deploy), the Lambda falls back to `default_state.json` bundled with the Lambda code. This contains the initial Hemma/Jobbet configuration. State is written back to S3 whenever the user modifies locations, stops, or trips through the API.

### State Schema

```json
{
  "locations": [
    {
      "id": "loc_home",
      "name": "Hemma",
      "lat": 59.270755,
      "lon": 18.114195,
      "address": "Skarpnäcks allé 34",
      "stops": [
        {"stop_id": "9091001000009140", "name": "Skarpnäck", "walk_minutes": 12}
      ]
    }
  ],
  "trips": [
    {
      "id": "trip_default",
      "name": "Jobbet",
      "origin_id": "loc_home",
      "destination_id": "loc_work"
    }
  ]
}
```

### Why not DynamoDB?

The app has a single user with a handful of locations and trips. A single JSON document is simpler to reason about, has no table schema to manage, and costs effectively nothing in S3. The entire state fits in a few KB.

---

## External APIs

### SL Journey Planner v2

See [sl-api.md](sl-api.md) for full API documentation.

- Base URL: `https://journeyplanner.integration.sl.se/v2`
- Authentication: None required
- Format: JSON

#### Trip Search (called at runtime by Lambda)

```
GET /v2/trips?type_origin=any&name_origin={origin_stop_id}&type_destination=any&name_destination={destination_stop_id}&calc_number_of_trips=3&calc_one_direction=true
```

#### Stop Finder — by name (development/debug)

```
GET /v2/stop-finder?name_sf={query}&type_sf=any&any_obj_filter_sf=2
```

#### Stop Finder — by coordinates (used for stop discovery, FR-14)

```
GET /v2/stop-finder?name_sf={lon}:{lat}:WGS84[dd.ddddd]&type_sf=coord&any_obj_filter_sf=2
```

The coordinate format is `longitude:latitude:WGS84[dd.ddddd]`. Note: longitude comes first.

Returns nearby stops with their global IDs, names, and coordinates. The Lambda uses the returned stop coordinates together with the location coordinates to calculate walking distance and estimate `walk_minutes`.

### Walking Time Calculation

Walking time is auto-calculated from the straight-line (Haversine) distance between the location and the stop, using an assumed walking speed of 5 km/h with a 1.3× detour factor to approximate real walking paths. The user can override this value manually.

### Geo-Location Resolution (FR-13)

Address-to-coordinate resolution uses the SL stop-finder endpoint with `type_sf=any` and `any_obj_filter_sf=12` (streets and addresses). The first result's coordinates are returned. No external geocoding service is needed.

```
GET /v2/stop-finder?name_sf={address}&type_sf=any&any_obj_filter_sf=12
```

---

## Lambda Logic — Layered Architecture (TR-8)

The Lambda handler is organized into layers so the API is reusable by other clients:

```
handler.py          # HTTP routing, request/response mapping
├── routes.py       # Route comparison business logic
├── state.py        # S3 state persistence (load/save)
└── models.py       # Domain entities, schemas, validation, helpers
```

Additional modules (locations CRUD, trips CRUD, geocoding, stop discovery) are added incrementally as vertical slices — designed API-first via OpenAPI, then implemented with tests.

### API Endpoints (current)

```
GET /api/routes?trip=<trip_id>[&reverse=true]
```

If `trip` is omitted, uses the first trip in the list. If `reverse=true`, origin and destination are swapped.

### API Endpoints (planned — not yet implemented)

These will be designed API-first (OpenAPI spec) and built as vertical slices when their UI increment needs them:

- Location + stop CRUD (FR-6)
- Trip CRUD + reorder (FR-15)
- Geocoding — address to coordinates (FR-13)
- Nearby stop discovery (FR-14)

### Routes Endpoint — Detailed Flow

1. Load state from S3
2. Resolve trip: use `trip` param or first trip in list
3. Look up origin and destination locations with their stops from state
4. If `reverse=true`, swap origin and destination
5. For each origin stop × destination stop combination, call SL Trip Planner:
   ```
   GET /v2/trips?type_origin=any&name_origin={origin_stop_id}&type_destination=any&name_destination={destination_stop_id}&calc_number_of_trips=3&calc_one_direction=true
   ```
6. Extract departure/arrival times, transport summary from response
7. Calculate `leave_by` = first leg departure − origin stop's `walk_minutes`
8. Calculate `arrive_by` = last leg arrival + destination stop's `walk_minutes`
9. Skip routes where `leave_by` is in the past
10. Sort by earliest `arrive_by`
11. Select two routes: fastest (earliest `arrive_by`), and from the rest, earliest `leave_by`
12. Flag fastest as `fastest: true`
13. Return JSON

### Routes Response Format

Each leg is a structured object with `line` (display name) and `mode` (transport type). The frontend maps `mode` to emoji icons (FR-11). Valid modes: `metro`, `bus`, `train`, `tram`, `walk`.

```json
{
  "generated_at": "2026-03-21T07:45:00+01:00",
  "trip_id": "trip_xyz789",
  "reversed": false,
  "origin": "Hemma",
  "destination": "Jobbet",
  "routes": [
    {
      "name": "Från Koloniområdet",
      "leave_by": "07:48",
      "departure": "07:51",
      "arrival": "08:37",
      "arrive_by": "08:39",
      "transfers": 2,
      "legs": [
        {"line": "816", "mode": "bus"},
        {"line": "17", "mode": "metro"},
        {"line": "41", "mode": "train"}
      ],
      "transfer_stations": ["Skarpnäck", "T-Centralen"],
      "fastest": true
    }
  ]
}
```

### Nearby Stops Response Format

```json
{
  "location_id": "loc_abc123",
  "stops": [
    {
      "stop_id": "9091001000009140",
      "name": "Skarpnäck",
      "walk_minutes": 12,
      "lat": 59.275,
      "lon": 18.127
    }
  ]
}
```

### Location Request/Response Format

```json
{
  "id": "loc_abc123",
  "name": "Hemma",
  "lat": 59.270755,
  "lon": 18.114195,
  "address": "Skarpnäcks allé 34",
  "stops": [
    {"stop_id": "9091001000009140", "name": "Skarpnäck", "walk_minutes": 12}
  ]
}
```

### Error Handling

- Unknown trip ID → HTTP 404
- Location not found → HTTP 404
- Invalid request body → HTTP 400
- Deleting a location referenced by a trip → cascading delete of those trips (FR-6)
- SL API failures → per-route error isolation (one failing route doesn't block others)
- All API calls fail → `{"error": "Could not fetch trip data", "routes": []}`

---

## Frontend

### Files

- `index.html` — single page, mobile-first layout
- `style.css` — styling

### Views

The frontend has two views, toggled via a simple tab/nav:

1. **Main view** — route comparison (default)
2. **Settings view** — manage locations, stops, and trips

### Main View Behavior

1. On load, fetch `GET /api/routes` (uses default trip)
2. Direction toggle: re-fetch with `&reverse=true` (FR-12). Labels derived from response `origin`/`destination` fields.
3. Render route cards sorted by arrival time
4. Fastest route visually highlighted (green border/background)
5. Each card shows:
   - Route name
   - "Leave by" time
   - Arrival time at final destination (`arrive_by`)
   - Transit legs with transport mode icons (e.g. "🚌 816 → 🚇 17 → 🚆 41")
   - Transfer stations (e.g. "Byte vid Skarpnäck, T-Centralen")
6. Refresh button reloads current direction
7. Loading and error states

### Settings View Behavior (planned)

Designed and built incrementally — see `todo.md` for delivery order.

### No Framework

Plain HTML + CSS + minimal vanilla JS. No build step.

---

## Secrets Management

The Trafiklab API key is stored in AWS Secrets Manager (FR-8). The secret name is passed to Lambda via the `SECRET_NAME` environment variable. Lambda reads the secret at runtime on cold start and caches it for the lifetime of the execution environment.

Note: The SL Journey Planner v2 API currently requires no API key. The secret is provisioned for future Trafiklab APIs that do require one (e.g. if the app expands to use ResRobot or other endpoints). The Lambda reads the secret but falls back gracefully if it's empty or absent.

---

## Project Structure

```
kiro-dev-workshop/
├── cdk/
│   ├── bin/app.ts                  # CDK app entry, instantiates both stacks
│   ├── lib/certificate-stack.ts    # ACM cert in us-east-1
│   ├── lib/app-stack.ts            # S3 buckets, Lambda, CloudFront, Route 53, Secrets Manager
│   ├── cdk.json
│   ├── package.json
│   └── tsconfig.json
├── lambda/
│   ├── handler.py                  # HTTP routing
│   ├── routes.py                   # Route comparison logic
│   ├── state.py                    # S3 state persistence (load/save)
│   ├── models.py                   # Domain entities, schemas, validation, helpers
│   ├── default_state.json          # Initial state (Hemma/Jobbet)
│   └── dev_server.py              # Local dev server with in-memory state
├── frontend/
│   ├── index.html
│   └── style.css
├── requirements.md
├── solution_design.md
└── sl-api.md
```

---

## Development Workflow

Each feature is delivered as a vertical slice through the stack:

1. **Domain modeling** — define or extend entities, schemas, and helpers in `models.py`
2. **API-first design** — specify the endpoint in `openapi.yaml` (request/response schemas, error codes) before writing any implementation
3. **Implement** — backend endpoint + handler routing
4. **Test** — unit tests with mocked dependencies
5. **Frontend** — UI that consumes the new endpoint
6. **Deploy and verify** — end-to-end against live environment

No stub endpoints. Features don't exist in the router until their increment builds them.

---

## Testing

### Unit Tests (pytest)

- Run with `cd lambda && python3 -m pytest`
- Test business logic in isolation: route comparison, walk time calculation, transfer deduplication
- External dependencies (SL API, S3) are mocked using `unittest.mock.patch`
- Time-dependent logic uses a fixed `datetime.now` via patching
- Test files live alongside source in `lambda/` (e.g. `test_routes.py`, `test_handler.py`)

### Integration Tests (local dev server)

- A local HTTP server (`lambda/dev_server.py`) serves the frontend on `http://localhost:8000` and proxies `/api/*` to the Lambda handler running locally
- Uses `default_state.json` as initial state, with an in-memory state store
- Manual browser testing to verify frontend ↔ API interaction
- Run with `cd lambda && python3 dev_server.py`

### Smoke Tests (post-deploy)

- Run after `./deploy.sh all` against the live endpoint
- A script (`smoke_test.sh`) that curls key endpoints and checks for expected HTTP status codes and response shapes

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| S3 state document | Single user with a handful of locations/trips. A single JSON file is simpler than DynamoDB, has no schema to manage, and costs effectively nothing. |
| Separate S3 buckets | Frontend bucket is public via CloudFront; state bucket is private with `BLOCK_ALL`. Prevents accidental exposure of app state. |
| State bucket RETAIN | State bucket is retained on stack delete to avoid losing user configuration. Frontend bucket is destroyed since it's regenerated from source. |
| Default state fallback | `default_state.json` bundled with Lambda provides initial config without a seeding step. First mutation writes to S3. |
| No API Gateway | CloudFront routes `/api/*` directly to Lambda function URL. Simpler and cheaper for a single-user app. |
| Secrets Manager for API key | FR-8 requires it. Provisioned even though SL v2 currently needs no key, for forward compatibility. |
| No caching | Every request triggers fresh API calls. Acceptable for a personal tool with infrequent use. |
| No authentication | Single-user personal tool (FR-7). |
| Separate CDK stacks | ACM certificate must be in us-east-1; keeping it in its own stack is cleaner than cross-region constructs. |
| SL stop-finder for geocoding | Avoids adding a third-party geocoding service. The SL API can resolve Stockholm addresses to coordinates. |
| SL stop-finder for nearby stops | The `type_sf=coord` parameter returns stops near given coordinates. No additional API needed. |
| Haversine + detour factor for walk time | Simple, no external routing API needed. 1.3× factor approximates real walking paths. User can override. |
| Layered Lambda modules | TR-8 requires the API to be reusable. Separating routing, CRUD, and state access makes the logic consumable by other clients. |
| jsonschema for validation | Single source of truth for input validation. Schemas live alongside domain entities in `models.py`. |
| `calc_number_of_trips=3` | Fetch a few trips per route to find one that's still catchable after accounting for walk time. |
| `calc_one_direction=true` | Prevents the planner from returning trips that depart before now. |
| OAC for both origins | Origin Access Control for S3 and Lambda function URL. |
| `Project: TripsApp` tag | NFR-6 requires all resources to be tagged for identification and cost tracking. |
| Cascading trip deletion | FR-6: deleting a location that is referenced by a trip automatically deletes that trip. Enforced in the locations module. |
| Trip ordering by list position | Trips are ordered by their position in the JSON array. Reorder endpoint accepts a list of trip IDs in desired order. |
