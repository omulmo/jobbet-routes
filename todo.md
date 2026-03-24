# Implementation Plan — Trips (trips.mulmo.name)

Each increment is a vertical slice: API + tests + OpenAPI + deploy/verify. No stub endpoints — features are designed API-first and built when needed.

---

## Increment 0: Domain modeling ✅

- [x] 0.1 — Domain entities: `Location`, `Stop`, `Trip`, `AppState` with serialization round-trip
- [x] 0.2 — JSON schemas for input validation (jsonschema)
- [x] 0.3 — Walking time calculation (Haversine + 1.3× detour factor)
- [x] 0.4 — Transfer station deduplication logic

## Increment 1: Core backend — route comparison ✅

- [x] 1.1 — CDK: S3 state bucket, Secrets Manager, Lambda bundling
- [x] 1.2 — `state.py` — S3 persistence with `default_state.json` fallback
- [x] 1.3 — `handler.py` — HTTP router (only `GET /api/routes` for now)
- [x] 1.4 — `routes.py` — Route comparison: `GET /api/routes?trip=<id>&reverse=true`
- [x] 1.5 — `models.py` — Domain entities, serialization, validation schemas, walk-time calc
- [x] 1.6 — `default_state.json` — initial Hemma/Jobbet config
- [x] 1.7 — Unit tests
- [x] 1.8 — `dev_server.py` — local dev server with in-memory state

## Increment 2: Ship core backend

- [x] 2.1 — OpenAPI spec (`openapi.yaml`) for `GET /api/routes`. Refactor the API so that emojis for transportation mode is a UI task, split leg into tuple (id,mode)
- [x] 2.2 - Update dev server to adhere to new spec
- [x] 2.3 - Update frontend code to reflect change in routes endpoint
- [x] 2.4 — Local testing: start dev server, verify API + frontend in browser
- [x] 2.5 — Deploy and verify end-to-end

## Increment 3: Dynamic main view

Replace hardcoded frontend with trip-driven route display. `GET /api/routes` already returns `trip_id`, `origin`, `destination`, `reversed` — enough for the direction toggle.

- [ ] 3.1 — Frontend: fetch `GET /api/routes`, render route results dynamically
- [ ] 3.2 — Direction toggle using response metadata (FR-12)
- [ ] 3.3 — Remove hardcoded `home`/`work` references
- [ ] 3.4 — Deploy and verify

## Increment 4: Settings UI — locations and trips

Design and build CRUD API endpoints API-first, then the UI that consumes them.

- [ ] 4.1 — Design CRUD API: locations, stops, trips (OpenAPI-first)
- [ ] 4.2 — Implement CRUD endpoints + unit tests
- [ ] 4.3 — Tab navigation: Main / Settings
- [ ] 4.4 — Location list with edit/delete
- [ ] 4.5 — Trip list with add (pick from existing locations), reorder, delete (FR-15)
- [ ] 4.6 — Style settings view, mobile-first
- [ ] 4.7 — Deploy and verify

## Increment 5: Geocoding — address to coordinates

Enable creating locations from an address.

- [ ] 5.1 — Design `GET /api/geocode` (OpenAPI-first)
- [ ] 5.2 — Implement geocode endpoint — SL API integration (FR-13)
- [ ] 5.3 — Unit tests
- [ ] 5.4 — Settings UI: "Add location" with address input + geocode resolve
- [ ] 5.5 — Settings UI: browser geolocation button as alternative (FR-13)
- [ ] 5.6 — Deploy and verify

## Increment 6: Nearby stop discovery

Enable discovering and adding stops to a location.

- [ ] 6.1 — Design `GET /api/locations/<id>/nearby-stops` (OpenAPI-first)
- [ ] 6.2 — Implement nearby-stops endpoint — SL stop-finder by coordinates, walk_minutes via Haversine (FR-14)
- [ ] 6.3 — Unit tests
- [ ] 6.4 — Settings UI: "Find nearby stops" button, select from results, editable walk_minutes (FR-14)
- [ ] 6.5 — Deploy and verify

## Increment 7: Rename and polish

- [x] 7.1 — CDK: rename stacks `Jobbet*` → `Trips*`, hostname `trips.mulmo.name`
- [x] 7.2 — Update `deploy.sh`, `setup-infrastructure.sh`, `deploy.env`
- [ ] 7.3 — Update `README.md`
- [ ] 7.4 — Update frontend title/heading
- [ ] 7.5 — Deploy and verify

## Increment 8: Smoke tests

- [ ] 8.1 — `smoke_test.sh` — curl key endpoints, check status codes + response shapes
