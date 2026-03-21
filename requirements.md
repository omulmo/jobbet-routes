# Requirements — Jobbet (jobbet.mulmo.name)

## Overview
A simple web app that helps a commuter in Stockholm decide when to leave home to get to work as fast as possible. The app compares multiple public transit route options using real-time data from Trafiklab APIs and recommends the fastest one.

---

## Functional Requirements

### FR-1: Real-Time Route Comparison
The app shall compare multiple pre-configured route options from home to work. Each route option represents a different way to commute, such as taking a bus from the nearest stop or walking to a metro station further away.

### FR-2: Estimated Arrival Time
For each route option, the app shall display the estimated arrival time at the destination if the user leaves home right now. This gives the user a clear picture of which option gets them to work the soonest.

### FR-3: Walking Time to Stop
Each route option shall include the estimated walking time from home to the departure stop. This ensures the user knows exactly when to walk out the door to catch the next departure.

### FR-4: Route Recommendation
The app shall highlight the fastest route option — the one with the earliest arrival time at work — so the user can make a quick decision at a glance.

### FR-5: Pull-Based Usage
The app is pull-based. The user opens the app in a browser to check departure suggestions. There are no push notifications or background alerts.

### FR-6: Static Route Configuration
Routes, stops, and destinations are statically configured in the application code or configuration files. There is no user-facing UI for changing routes or settings.

### FR-7: Single User
The app is designed for a single user. There is no authentication, user accounts, or multi-tenancy.

### FR-8: Trafiklab API Integration
The app shall retrieve real-time public transit data from Trafiklab APIs (SL Reseplanerare / Trip Planner and/or SL Realtidsinformation). The API key is stored in AWS Secrets Manager and retrieved by the backend at runtime.

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
The CDK stack creates an ACM certificate for `jobbet.mulmo.name` in the `us-east-1` region (required by CloudFront). DNS validation is performed against the existing Route 53 hosted zone for `mulmo.name`.

### TR-6: Domain and DNS
The domain `jobbet.mulmo.name` is used to access the app. The CDK stack creates an alias record in the existing Route 53 hosted zone for `mulmo.name`, pointing to the CloudFront distribution.

### TR-7: Secrets Management
The Trafiklab API key is stored in AWS Secrets Manager. The Lambda function has IAM permissions to read the secret at runtime. The API key is never hardcoded in source code or environment variables.
