# Project Brief

## Project Name
Trips — trips.mulmo.name (formerly Jobbet / jobbet.mulmo.name)

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
- External API: SL Journey Planner v2 + stop lookup APIs
- Persistence for locations, stops, and trips (mechanism TBD in solution design)

## Status
Bidirectional routing (home↔work) is implemented and deployed. Requirements updated for location CRUD, stop discovery, geo-location, trip management, and persistence. Solution design update pending.
