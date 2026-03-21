# Progress

## What Works
- Full infrastructure deployed via CDK (ACM cert, S3, Lambda, CloudFront, Route 53)
- CloudFront → S3 with OAC (static frontend)
- CloudFront → Lambda function URL with OAC (API)
- Both `lambda:InvokeFunctionUrl` and `lambda:InvokeFunction` permissions granted
- Fast deploy script for code iteration
- Infrastructure setup script with configurable hostname
- Git repo initialized and pushed to GitHub

## What's Left
- Lambda handler logic (calling SL Journey Planner v2 API, parsing responses)
- Frontend UI (route cards, loading/error states, refresh)
- End-to-end testing with real API data

## Known Issues
- `npx cdk` swallows stdout — must use `./node_modules/.bin/cdk` directly
- Lambda `process_route` had bare `except Exception` swallowing all errors — now logged
- Zero routes often caused by all departures being in the past (leave_by < now), not API failures
