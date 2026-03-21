# Solution Design — Jobbet (jobbet.mulmo.name)

## Architecture

```
User (mobile browser)
  → jobbet.mulmo.name (Route 53 alias)
  → CloudFront (single distribution)
      ├── /api/*  → Lambda Function URL (Python, eu-north-1)
      └── /*      → S3 bucket (static HTML + CSS)
```

## AWS Resources

### CertificateStack (us-east-1)

- ACM certificate for `jobbet.mulmo.name`
- DNS validation against the existing `mulmo.name` Route 53 hosted zone
- Exports the certificate ARN via `CfnOutput` for cross-stack reference

### AppStack (eu-north-1)

- S3 bucket for static frontend assets (HTML + CSS)
- Lambda function (Python 3.12) with function URL enabled
- CloudFront distribution with two behaviors:
  - Default behavior → S3 origin with Origin Access Control (OAC)
  - `/api/*` behavior → Lambda function URL origin with OAC
- Custom domain `jobbet.mulmo.name` with ACM certificate from CertificateStack
- Route 53 A-record alias: `jobbet.mulmo.name` → CloudFront distribution
- Imports the existing `mulmo.name` hosted zone via `HostedZone.fromLookup()`

### Cross-Stack Reference

The CertificateStack exports the ACM certificate ARN. The AppStack imports it using `Fn.importValue()`. Both stacks are instantiated in the same CDK app (`bin/app.ts`), with an explicit dependency so the certificate is created before the distribution.

---

## External API: SL Journey Planner v2

See [sl-api.md](sl-api.md) for full API documentation, including endpoint details, response structure, and known quirks.

### Overview

- Provider: Trafiklab / SL
- Base URL: `https://journeyplanner.integration.sl.se/v2`
- Authentication: None required (no API key)
- Format: JSON
- Rate limiting: No formal limit, but excessive requests should be avoided

### Endpoints Used

#### Stop Finder (used during development to look up stop IDs)

```
GET /v2/stop-finder?name_sf={query}&type_sf=any&any_obj_filter_sf=2
```

Not called at runtime — only used to resolve stop IDs during configuration.

#### Trip Search (called at runtime by Lambda)

```
GET /v2/trips?type_origin=any&name_origin={origin_id}&type_destination=any&name_destination={destination_id}&calc_number_of_trips=1&calc_one_direction=true
```

Parameters:
| Parameter | Value | Description |
|-----------|-------|-------------|
| `type_origin` | `any` | Origin is a stop ID |
| `name_origin` | e.g. `9091001000001835` | Global stop ID for departure stop |
| `type_destination` | `any` | Destination is a stop ID |
| `name_destination` | `9091001001009509` | Global stop ID for Solna station |
| `calc_number_of_trips` | `1` | Return 1 trip per request |
| `calc_one_direction` | `true` | Only return trips departing after now |

### Example API Request

```
GET https://journeyplanner.integration.sl.se/v2/trips?type_origin=any&name_origin=9091001000001835&type_destination=any&name_destination=9091001001009509&calc_number_of_trips=1&calc_one_direction=true
```

### Example API Response (abbreviated)

The response contains a `journeys` array. Each journey has `legs` (segments of the trip). A journey from Skarpnäcks koloniområde to Solna station might have 5 legs:

```json
{
  "journeys": [
    {
      "tripDuration": 2880,
      "interchanges": 2,
      "legs": [
        {
          "origin": {
            "name": "Skarpnäcks koloniområde, Stockholm",
            "parent": { "name": "Skarpnäcks koloniområde, Stockholm" },
            "departureTimePlanned": "2026-03-21T08:49:00Z",
            "departureTimeEstimated": "2026-03-21T08:49:00Z"
          },
          "destination": {
            "name": "Skarpnäck (på Horisontvägen), Stockholm",
            "parent": { "name": "Skarpnäck (på Horisontvägen), Stockholm" },
            "arrivalTimePlanned": "2026-03-21T08:53:00Z",
            "arrivalTimeEstimated": "2026-03-21T08:53:00Z"
          },
          "transportation": {
            "name": "Buss Buss 816",
            "disassembledName": "816",
            "product": { "name": "Buss" }
          }
        },
        {
          "origin": { "departureTimePlanned": "2026-03-21T08:58:12Z" },
          "destination": { "arrivalTimePlanned": "2026-03-21T09:04:12Z" },
          "transportation": { "product": { "name": "Gång" } }
        },
        {
          "origin": {
            "name": "Skarpnäck, Stockholm",
            "departureTimePlanned": "2026-03-21T09:04:12Z"
          },
          "destination": {
            "name": "T-Centralen, Stockholm",
            "arrivalTimePlanned": "2026-03-21T09:23:00Z"
          },
          "transportation": {
            "name": "Tunnelbana tunnelbanans gröna linje 17",
            "disassembledName": "17"
          }
        },
        {
          "origin": { "departureTimePlanned": "2026-03-21T09:24:00Z" },
          "destination": { "arrivalTimePlanned": "2026-03-21T09:30:00Z" },
          "transportation": { "product": { "name": "Gång" } }
        },
        {
          "origin": {
            "name": "Stockholm City, Stockholm",
            "departureTimePlanned": "2026-03-21T09:30:00Z"
          },
          "destination": {
            "name": "Solna, Solna",
            "arrivalTimePlanned": "2026-03-21T09:37:00Z",
            "arrivalTimeEstimated": "2026-03-21T09:37:00Z"
          },
          "transportation": {
            "name": "Tåg Pendeltåg 41",
            "disassembledName": "41"
          }
        }
      ]
    }
  ]
}
```

### Key Response Fields

| Field | Description |
|-------|-------------|
| `journeys[].tripDuration` | Total trip duration in seconds |
| `journeys[].interchanges` | Number of transfers |
| `journeys[].legs[]` | Array of trip segments (transit + walking) |
| `legs[].origin.departureTimeEstimated` | Real-time departure (falls back to `departureTimePlanned`) |
| `legs[].destination.arrivalTimeEstimated` | Real-time arrival (falls back to `arrivalTimePlanned`) |
| `legs[].transportation.name` | Full transport name (e.g. "Tunnelbana tunnelbanans gröna linje 17") |
| `legs[].transportation.disassembledName` | Short line number (e.g. "17") |
| `legs[].transportation.product.name` | Transport type (e.g. "Tunnelbana", "Buss", "Tåg") |

---

## Route Configuration

Defined as a static Python dict in the Lambda handler:

```python
DESTINATION_ID = "9091001001009509"  # Solna station

ROUTES = [
    {"name": "Buss från Koloniområdet",      "walk_minutes": 3,  "origin_id": "9091001000001835"},
    {"name": "T-bana från Skarpnäck",        "walk_minutes": 12, "origin_id": "9091001000009140"},
    {"name": "T-bana från Skogskyrkogården", "walk_minutes": 15, "origin_id": "9091001000009185"},
]
```

### Stop Reference

| Stop | Global ID | Type |
|------|-----------|------|
| Skarpnäcks koloniområde | `9091001000001835` | Bus stop |
| Skarpnäck (t-banan) | `9091001000009140` | Metro station |
| Skogskyrkogården | `9091001000009185` | Metro station |
| Solna station (destination) | `9091001001009509` | Commuter rail station |

Home address: Lugna gatan 15, 128 38 Skarpnäck (lat 59.270755, lon 18.114195).

---

## Lambda Logic

### Endpoint

`GET /api/routes`

### Flow

1. For each route in `ROUTES`, call the SL Trip Planner API:
   ```
   GET /v2/trips?type_origin=any&name_origin={origin_id}&type_destination=any&name_destination=9091001001009509&calc_number_of_trips=1&calc_one_direction=true
   ```
2. From the response, extract:
   - First leg's departure time (when transit departs from the origin stop)
   - Last leg's arrival time (when you arrive at Solna station)
   - Transport summary (line names for each non-walking leg)
3. Calculate "leave home by" = first leg departure time − walk_minutes
4. Skip the route if "leave home by" is already in the past
5. Sort remaining routes by earliest arrival time
6. Select two routes: the fastest (earliest arrival), and from the rest, the one with the earliest "leave home by" time
7. Flag the fastest route as `fastest: true`
8. Return JSON

### Response Format

```json
{
  "generated_at": "2026-03-21T07:45:00+01:00",
  "routes": [
    {
      "name": "Buss från Koloniområdet",
      "walk_minutes": 3,
      "leave_home_by": "07:48",
      "departure": "07:51",
      "arrival": "08:37",
      "transfers": 2,
      "legs": ["Buss 816", "T17", "Pendeltåg 41"],
      "fastest": true
    },
    {
      "name": "T-bana från Skarpnäck",
      "walk_minutes": 12,
      "leave_home_by": "07:40",
      "departure": "07:52",
      "arrival": "08:42",
      "transfers": 1,
      "legs": ["T17", "Pendeltåg 41"],
      "fastest": false
    }
  ]
}
```

### Error Handling

- If the SL API returns no journeys for a route, that route is omitted from the response
- If all API calls fail, return `{"error": "Could not fetch trip data", "routes": []}`
- HTTP errors from the SL API are caught per-route (one failing route doesn't block others)

---

## Frontend

### Files

- `index.html` — single page, mobile-first layout
- `style.css` — styling

### Behavior

1. On page load, fetch `/api/routes` via `fetch()`
2. Render route cards sorted by arrival time
3. Fastest route is visually highlighted (e.g. green border or background)
4. Each card shows:
   - Route name
   - "Leave home by" time
   - Departure time from stop
   - Arrival time at Solna
   - Transit legs (e.g. "Buss 816 → T17 → Pendeltåg 41")
5. Refresh button calls `location.reload()`
6. Loading state while fetching
7. Error state if fetch fails

### No Framework

Plain HTML + CSS + minimal vanilla JS (only for fetch + DOM rendering + refresh button). No build step.

---

## Project Structure

```
kiro-dev-workshop/
├── cdk/
│   ├── bin/app.ts                  # CDK app entry, instantiates both stacks
│   ├── lib/certificate-stack.ts    # ACM cert in us-east-1
│   ├── lib/app-stack.ts            # S3, Lambda, CloudFront, Route 53 in eu-north-1
│   ├── cdk.json
│   ├── package.json
│   └── tsconfig.json
├── lambda/
│   └── handler.py
├── frontend/
│   ├── index.html
│   └── style.css
├── requirements.md
└── solution_design.md
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| No API Gateway | CloudFront routes `/api/*` directly to Lambda function URL. Simpler and cheaper for a single-user app. |
| No Secrets Manager | SL Journey Planner v2 requires no API key. |
| No caching | Every request triggers fresh API calls. Acceptable for a personal tool with infrequent use. |
| No authentication | Single-user personal tool. |
| Separate CDK stacks | ACM certificate must be in us-east-1; keeping it in its own stack is cleaner than cross-region constructs. |
| Static route config | Routes defined as a Python dict in the Lambda code. No database needed. |
| OAC for both origins | Origin Access Control for S3 and Lambda function URL. More security can be added later. |
| `calc_number_of_trips=1` | We only need the next available trip per route. Keeps responses small and fast. |
| `calc_one_direction=true` | Prevents the planner from returning trips that depart before now. |
