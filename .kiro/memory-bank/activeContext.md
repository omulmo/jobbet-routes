# Active Context

## Current Focus
Increment 2 complete. Next: Increment 3 — dynamic main view (trip-driven route display).

## Recent Changes
- Created `openapi.yaml` for `GET /api/routes` (API-first design)
- Refactored API: legs are now structured `{line, mode}` objects instead of emoji strings — emoji rendering is a frontend concern (FR-11)
- Replaced `ICON_*` emoji constants and `MODE_ICONS` in `routes.py` with `MODE_MAP` returning semantic mode names
- Frontend renders emojis via `MODE_ICONS` JS mapping and `fmtLeg()` helper
- Updated `solution_design.md` with new routes response format
- Fixed `deploy.sh`: `pip` → `pip3`, include `*.json` in Lambda package

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
- Walking man emoji needs ZWJ chars — use `\u200D\u27A1\uFE0F` suffix in frontend JS
- ZWJ right-facing trick only works on person emojis (🚶), not vehicle emojis (🚌🚇🚆🚊)
- Emoji rendering is a frontend concern — API returns semantic mode names, not emoji strings
- `npx cdk` swallows stdout — use `./node_modules/.bin/cdk` directly
- SL stop-finder coordinate format: longitude comes first (`lon:lat:WGS84[dd.ddddd]`)
