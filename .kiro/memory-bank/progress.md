# Progress

## What Works
- Domain model: Location, Stop, Trip, AppState with serialization, validation, walk-time calc, transfer dedup
- `GET /api/routes` endpoint: fetches SL API for all stop combinations, selects fastest + next departure
- OpenAPI spec (`openapi.yaml`) for `GET /api/routes`
- API returns structured legs `{line, mode}` — frontend maps mode to emoji icons
- S3 state persistence with `default_state.json` fallback
- HTTP router (handler.py) dispatching to routes module
- Local dev server with in-memory state
- Frontend renders route cards with emoji icons via JS `MODE_ICONS` mapping
- 38 unit tests passing (models, state, routes, handler)
- CDK stack compiles (S3 buckets, Lambda, CloudFront, Route 53, Secrets Manager)

## What's Been Scrapped
- `locations.py`, `trips.py` — CRUD modules built bottom-up without consumers. Will be redesigned API-first when the settings UI increment needs them.
- DynamoDB — replaced with S3 single JSON document early in development.

## What's Next (see todo.md)
- Increment 2: Deploy pending (AWS session expired) — run `aws login` then `./deploy.sh all`
- Increment 3: Dynamic main view (trip-driven route display)
- Increment 3: Dynamic main view (trip-driven route display)
- Increment 4: Settings UI + CRUD API (designed API-first)
- Increment 5: Geocoding
- Increment 6: Nearby stop discovery
- Increment 7: Rename jobbet → trips
- Increment 8: Smoke tests

## Known Issues
- `npx cdk` swallows stdout — must use `./node_modules/.bin/cdk` directly
- SL API `calc_number_of_trips` max is 3 (4+ returns HTTP 400)
- `leg.origin.disassembledName` at transfers = platform ID, not station name
- CDK stack names still say `Jobbet*` — rename deferred to increment 7
