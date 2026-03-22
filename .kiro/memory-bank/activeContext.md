# Active Context

## Current Focus
- Requirements updated for location CRUD, stop discovery, geo-location, trip management, persistence, and layered architecture
- Domain changing from `jobbet.mulmo.name` to `trips.mulmo.name`
- Solution design update is the next step — needs to address persistence, new API endpoints, stop discovery API, geo-location resolution, and frontend views for managing locations/stops/trips

## Recent Changes
- Added bidirectional routing: LOCATIONS dict with home/work, `from`/`to` query params, `arrive_by` with destination walk time
- Added direction toggle UI with context-aware labels
- Updated requirements: FR-6 (CRUD locations), FR-12 (trip-based toggle), FR-13 (geo-location), FR-14 (stop discovery), FR-15 (trips), FR-16 (persistence), TR-8 (layered architecture)
- Renamed app from "Jobbet" to "Trips", domain from `jobbet.mulmo.name` to `trips.mulmo.name`
- Updated resource tag from `JobbetApp` to `TripsApp`

## Active Decisions
- Using `deploy.sh` for fast code iteration (bypasses CloudFormation)
- Persistence mechanism deferred to solution design (FR-16)
- Direction toggle derived from first trip in ordered list + its reverse (FR-12, FR-15)
- Walk minutes: auto-calculated from geo-distance, user-overridable (FR-14)
- Location delete cascades to trips referencing it (FR-6)

## Known Gotchas
- SL Journey Planner v2 `calc_number_of_trips` max is 3 (4+ returns 400)
- `leg.origin.disassembledName` at transfer points contains platform IDs ("Z", "1"), not station names — use `parent.disassembledName` instead
- Walking man emoji needs ZWJ chars — always use the named constant `ICON_WALK`
- `npx cdk` swallows stdout — use `./node_modules/.bin/cdk` directly

## Workflow Reminders
- On commit: reflect → update memory bank → commit → push
- Development workflow: requirements → solution design → implementation → tests → deploy → integration test
