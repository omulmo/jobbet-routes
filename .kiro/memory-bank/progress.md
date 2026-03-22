# Progress

## What Works
- Full infrastructure deployed via CDK (ACM cert, S3, Lambda, CloudFront, Route 53)
- CloudFront → S3 with OAC (static frontend)
- CloudFront → Lambda function URL with OAC (API)
- Two-route selection: fastest arrival + earliest departure from remaining routes
- Lambda fetches 3 trips per route, iterates to find first catchable departure
- Transfer station display with deduplication (FR-9, FR-10)
- Transport mode icons on legs: 🚇 metro, 🚌 bus, 🚆 train, 🚊 tram (FR-11)
- All emoji in Python code use named unicode escape constants
- SVG favicon with 🚉 emoji
- Fast deploy script for code iteration
- Unit tests passing (7/7)
- Git repo at github.com/omulmo/jobbet-routes.git

## What's Left
- Consider edge cases for two-route selection (e.g. when both picks are the same route)
- End-to-end testing during weekday morning commute hours

## Recently Fixed
- Timezone: replaced hardcoded UTC+1 with `ZoneInfo("Europe/Stockholm")` — now handles CET↔CEST automatically

## Known Issues
- `npx cdk` swallows stdout — must use `./node_modules/.bin/cdk` directly
- SL API `calc_number_of_trips` max is 3 (4+ returns HTTP 400)
- `leg.origin.disassembledName` at transfers = platform ID, not station name
