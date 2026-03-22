# Progress

## What Works
- Full infrastructure deployed via CDK (ACM cert, S3, Lambda, CloudFront, Route 53)
- CloudFront → S3 with OAC (static frontend)
- CloudFront → Lambda function URL with OAC (API)
- Bidirectional routing: `from`/`to` query params, LOCATIONS dict with home and work
- `arrive_by` calculation includes destination stop walk_minutes
- Direction toggle UI ("→ Jobbet" / "→ Hemma") with context-aware labels
- Two-route selection: fastest arrival + earliest departure from remaining routes
- Lambda fetches 3 trips per route, iterates to find first catchable departure
- Transfer station display with deduplication (FR-9, FR-10)
- Transport mode icons on legs: 🚇 metro, 🚌 bus, 🚆 train, 🚊 tram (FR-11)
- Route names derived from origin stop ("Från Koloniområdet")
- HTTP 400 for unknown location keys
- All emoji in Python code use named unicode escape constants
- SVG favicon with 🚉 emoji
- Fast deploy script for code iteration
- Live at https://jobbet.mulmo.name

## What's Next
- Solution design update for: persistence layer, CRUD API endpoints, stop discovery API, geo-location resolution, trip management, frontend management views, layered architecture (TR-8)
- Infrastructure changes: rename to trips.mulmo.name, add persistence (DynamoDB or similar), possibly new API endpoints
- Implementation of FR-6 (location CRUD), FR-13 (geo-location), FR-14 (stop discovery), FR-15 (trips), FR-16 (persistence)

## Known Issues
- `npx cdk` swallows stdout — must use `./node_modules/.bin/cdk` directly
- SL API `calc_number_of_trips` max is 3 (4+ returns HTTP 400)
- `leg.origin.disassembledName` at transfers = platform ID, not station name
