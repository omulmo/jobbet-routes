# Active Context

## Current Focus
- Application is deployed and live at https://jobbet.mulmo.name
- Fixed timezone handling: uses `ZoneInfo("Europe/Stockholm")` for automatic CET↔CEST

## Recent Changes
- Replaced hardcoded `timezone(timedelta(hours=1))` with `ZoneInfo("Europe/Stockholm")` to survive DST switch on March 29

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
