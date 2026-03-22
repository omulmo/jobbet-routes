# Requirements — Trips (trips.mulmo.name)

## Overview
A simple web app that helps a commuter in Stockholm decide when to leave for a destination as fast as possible. The app compares multiple public transit route options using real-time data from Trafiklab APIs and recommends the fastest one. The user manages their own locations, stops, and trips through the UI.

---

## Functional Requirements

### FR-1: Real-Time Route Comparison
The app shall compare multiple route options between two locations based on the active trip. Each route option represents a different way to commute, such as taking a bus from the nearest stop or walking to a metro station further away.

### FR-2: Estimated Arrival Time
For each route option, the app shall display the estimated arrival time at the final destination (including walking time from the arrival stop) if the user leaves right now.

### FR-3: Walking Time to Stop
Each route option shall include the estimated walking time from the origin location to the departure stop, so the user knows when to walk out the door.

### FR-4: Route Recommendation
The app shall return exactly two route options:
1. The fastest route — the one with the earliest arrival time at the destination.
2. The next departure — from the remaining routes, the one with the earliest "leave by" time.

If only one valid route exists, only one is returned. The fastest route is visually highlighted so the user can make a quick decision at a glance.

### FR-5: Pull-Based Usage
The app is pull-based. The user opens the app in a browser to check departure suggestions. There are no push notifications or background alerts.

### FR-6: Location Management (CRUD)
The user can create, view, update, and delete locations through the UI. Each location has a display name, geo-coordinates (latitude/longitude), and zero or more associated transit stops. Deleting a location that is referenced by a trip automatically deletes that trip.

### FR-7: Single User
The app is designed for a single user. There is no authentication, user accounts, or multi-tenancy.

### FR-8: Trafiklab API Integration
The app shall retrieve real-time public transit data from Trafiklab APIs (SL Reseplanerare / Trip Planner and/or SL Realtidsinformation). The API key is stored in AWS Secrets Manager and retrieved by the backend at runtime.

### FR-9: Transfer Station Display
For each route option, the app shall display the names of the stations where the user transfers between transport modes (e.g. bus to metro, metro to commuter train). This helps the user understand the journey at a glance.

### FR-10: Deduplicated Transfer Stations
Transfer station names shall be deduplicated so that consecutive transfers at the same station (e.g. walking between platforms) appear only once. Near-duplicate names where one contains the other (e.g. "Odenplan" and "Stockholm Odenplan") shall be collapsed to the shorter name.

### FR-11: Transport Mode Icons
Each transit leg shall display a small icon indicating the mode of transportation (e.g. metro, bus, train) alongside the line number.

### FR-12: Direction Selection
The direction toggle is derived from the first trip in the user's ordered trip list. The toggle shows the first trip and its reverse (e.g. "→ Jobbet" / "→ Hemma"). When reversed, origin and destination are swapped and walking times are taken from the respective location's stops.

### FR-13: Geo-Location Resolution
When creating or editing a location, the user can use the browser's geolocation API to set coordinates automatically, or enter an address that the backend resolves to latitude/longitude.

### FR-14: Stop Discovery
When adding stops to a location, the backend provides a lookup of nearby transit stops based on the location's geo-coordinates. The user selects from discovered stops. Walking time (in minutes) is auto-calculated from the distance between the location and the stop, but the user can override it manually.

### FR-15: Trip Configuration
A trip is an ordered pair of locations (origin → destination). The user can create, reorder, and delete trips. The first trip in the ordered list determines the direction toggle on the main view. Trips reference locations by identity.

### FR-16: Persistence
Locations, stops, and trips are persisted so that configuration survives across sessions and deployments. The persistence mechanism is a solution design concern.

---

## Non-Functional Requirements

### NFR-1: Availability
Availability requirements are low. The app is a personal tool and occasional downtime is acceptable. There is no need for multi-region redundancy or health checks.

### NFR-2: Performance
A response time of a few seconds is acceptable. The backend calls an external API on every request, so latency depends partly on Trafiklab's response time.

### NFR-3: User Interface
The frontend is a simple, mobile-first HTML + CSS page with no JavaScript framework. It should be easy to read on a phone screen since the primary use case is checking the app before leaving home.

### NFR-4: Cost
The application shall run on AWS serverless infrastructure to minimize cost. There should be no always-on compute resources. Pay-per-request pricing is preferred.

### NFR-5: No Caching
The initial implementation does not cache API responses. Every request to the backend triggers a fresh call to the Trafiklab API. Caching may be added later as an optimization.

### NFR-6: Resource Tagging
All AWS resources in this project shall be tagged with `Project: TripsApp` so that relevant resources can be easily identified and tracked across the AWS account.

---

## Technical Requirements

### TR-1: Frontend Hosting
The static frontend (HTML + CSS) is hosted in an S3 bucket and served through CloudFront. CloudFront handles HTTPS termination and caching of static assets.

### TR-2: Backend
The backend is a Python AWS Lambda function. It receives requests from CloudFront, retrieves the Trafiklab API key from Secrets Manager, calls the Trafiklab API, and returns route suggestions as JSON.

### TR-3: CloudFront Routing
A single CloudFront distribution serves both the frontend and backend:
- Requests to `/api/*` are routed to the Lambda function URL origin.
- All other requests are routed to the S3 origin for static content.

There is no API Gateway — CloudFront connects directly to the Lambda function URL.

### TR-4: Infrastructure as Code
All infrastructure is defined using AWS CDK in TypeScript. The CDK stack provisions the S3 bucket, Lambda function, CloudFront distribution, ACM certificate, Route 53 record, and Secrets Manager access. The primary deployment region is `eu-north-1` (Stockholm), with the exception of the ACM certificate which must be in `us-east-1` for CloudFront.

### TR-5: SSL Certificate
The CDK stack creates an ACM certificate for `trips.mulmo.name` in the `us-east-1` region (required by CloudFront). DNS validation is performed against the existing Route 53 hosted zone for `mulmo.name`.

### TR-6: Domain and DNS
The domain `trips.mulmo.name` is used to access the app. The CDK stack creates an alias record in the existing Route 53 hosted zone for `mulmo.name`, pointing to the CloudFront distribution.

### TR-7: Secrets Management
The Trafiklab API key is stored in AWS Secrets Manager. The Lambda function has IAM permissions to read the secret at runtime. The API key is never hardcoded in source code or environment variables.

### TR-8: Layered Architecture
The solution shall separate presentation logic (frontend) from data-oriented APIs that use domain primitives (locations, stops, trips). The API and business logic layer shall be reusable by other clients, such as alternative UIs or an MCP agent.
