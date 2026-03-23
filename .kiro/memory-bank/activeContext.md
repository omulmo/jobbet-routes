# Active Context

## Current Focus
Increment 2: ship core backend. OpenAPI spec for `GET /api/routes`, local testing, then deploy.

## Recent Changes
- Restructured development workflow to vertical slices: requirements → solution design (incl. domain modeling) → API-first (OpenAPI) → implement → test → frontend → deploy
- Scrapped pre-built CRUD modules (`locations.py`, `trips.py`) and their tests — they were built bottom-up without consumers, will be redesigned API-first when needed
- Stripped `handler.py` to only `GET /api/routes` — no stub endpoints
- Updated `todo.md` to incremental vertical slices
- Updated `solution_design.md` to reflect current state (no unbuilt features described as existing)
- Updated `.kiro/rules/development-workflow.md` with the new workflow
- 38 unit tests passing

## Active Decisions
- S3 single JSON document for persistence (not DynamoDB — too complex for single user)
- Domain primitives defined in `solution_design.md` (source of truth), implemented in `models.py`
- No stub endpoints — features built API-first when their increment needs them
- Two separate S3 buckets: public frontend, private state (security separation)
- State falls back to `default_state.json` when no S3 state exists
- SL stop-finder for both nearby-stop discovery and address geocoding (no external services)
- Secrets Manager provisioned for forward compatibility (SL v2 currently needs no key)

## Known Gotchas
- SL Journey Planner v2 `calc_number_of_trips` max is 3 (4+ returns 400)
- `leg.origin.disassembledName` at transfer points = platform ID, not station name — use `parent.disassembledName`
- Walking man emoji needs ZWJ chars — always use the named constant `ICON_WALK`
- `npx cdk` swallows stdout — use `./node_modules/.bin/cdk` directly
- SL stop-finder coordinate format: longitude comes first (`lon:lat:WGS84[dd.ddddd]`)
