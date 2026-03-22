# Active Context

## Current Focus
- Application is deployed and live at https://jobbet.mulmo.name
- Transfer station display and transport mode icons implemented and deployed

## Recent Changes
- FR-9: Transfer station display — shows "Byte vid X, Y" for each route
- FR-10: Deduplicated transfer stations — collapses same/near-duplicate names (e.g. "Odenplan" + "Stockholm Odenplan" → "Odenplan")
- FR-11: Transport mode icons — emoji icons (🚇🚌🚆🚊) prepended to line numbers in legs
- All emoji in handler.py replaced with named `\uXXXX` constants (ICON_WALK, ICON_METRO, etc.)
- Removed ⭐ from fastest route card (green highlight is sufficient)
- Updated requirements.md, solution_design.md, and tests for all changes

## Active Decisions
- Using `deploy.sh` for fast code iteration (bypasses CloudFormation)
- Using `setup-infrastructure.sh` for full CDK deploys
- Resource names stored in `deploy.env` (gitignored)
- Transfer station names sourced from `leg.origin.parent.disassembledName` (not `disassembledName` which contains platform IDs)

## Known Gotchas
- SL Journey Planner v2 `calc_number_of_trips` max is 3 (4+ returns 400)
- `leg.origin.disassembledName` at transfer points contains platform IDs ("Z", "1"), not station names — use `parent.disassembledName` instead
- Walking man emoji needs ZWJ chars — always use the named constant `ICON_WALK`
- `lambda/` dir name is a Python keyword — use `importlib.util` for local testing
- `str_replace` can fail on emoji characters — use `sed` or `insert` as fallback

## Workflow Reminders
- On commit: reflect → update memory bank → commit → push
- Development workflow: requirements → solution design → implementation → tests → deploy → integration test
