# Project Brief

## Project Name
Trips — trips.mulmo.name

## Overview
A personal commuter app for Stockholm. Compares real-time public transit routes between user-defined locations in both directions, and recommends the fastest option. The user manages locations, stops, and trips through the UI.

## Goals
- Show the fastest way to get between two locations using Stockholm public transit
- Let the user configure their own locations with nearby transit stops
- Support bidirectional trips (e.g. home→work and work→home)
- Keep it simple: single user, no auth, serverless, minimal cost

## Scope
- Frontend: mobile-first static HTML/CSS/JS (no framework)
- Backend: Python Lambda behind CloudFront
- Infrastructure: AWS CDK (TypeScript)
- External API: SL Journey Planner v2 (trip search, stop finder by name and coordinates)
- Persistence: DynamoDB single-table design for locations, stops, and trips

## Relationship to Jobbet
Trips is a new deployment, not a migration. The old Jobbet app (`jobbet.mulmo.name`) remains deployed as-is. Its CDK identifiers are recorded in `cdk.md` for future teardown.
