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

## Location Configuration

Defined as a static Python dict in the Lambda handler. Each location has a display name, geo-coordinates, and one or more associated transit stops with walking distances:

```python
LOCATIONS = {
    "home": {
        "name": "Hemma",
        "lat": 59.270755,
        "lon": 18.114195,
        "stops": [
            {"name": "Koloniområdet",    "id": "9091001000001835", "walk_minutes": 3},
            {"name": "Skarpnäck",        "id": "9091001000009140", "walk_minutes": 12},
            {"name": "Skogskyrkogården", "id": "9091001000009185", "walk_minutes": 15},
        ],
    },
    "work": {
        "name": "Jobbet",
        "lat": 59.360031,
        "lon": 18.000109,
        "stops": [
            {"name": "Solna station", "id": "9091001001009509", "walk_minutes": 2},
        ],
    },
}
```

Routes are derived at runtime by pairing each origin location stop with the destination location's stop(s). The `from` and `to` query parameters select which location is origin and which is destination.

### Walk Minutes Logic

Every stop has a `walk_minutes` value representing the walking time between that stop and its parent location. Both ends of a trip may involve walking, so both origin and destination walk times are always accounted for:

- `leave_by` = first leg departure time − origin stop's `walk_minutes` (walk from starting point to departure stop)
- `arrive_by` = last leg arrival time + destination stop's `walk_minutes` (walk from arrival stop to final destination)

Example for `from=home&to=work`:
- Origin stop: Skarpnäck (walk_minutes: 12) → leave home 12 min before departure
- Destination stop: Solna station (walk_minutes: 2) → arrive at office 2 min after train arrives

Example for `from=work&to=home`:
- Origin stop: Solna station (walk_minutes: 2) → leave office 2 min before departure
- Destination stop: Skarpnäck (walk_minutes: 12) → arrive home 12 min after metro arrives

Since routes are derived by pairing origin stops with destination stops, and each location may have multiple stops, the walk times on both sides can vary per route combination.

The route name is derived from the origin stop: e.g. "Från Koloniområdet" or "Från Solna station".

### Stop Reference

| Stop | Global ID | Type | Location |
|------|-----------|------|----------|
| Skarpnäcks koloniområde | `9091001000001835` | Bus stop | home |
| Skarpnäck (t-banan) | `9091001000009140` | Metro station | home |
| Skogskyrkogården | `9091001000009185` | Metro station | home |
| Solna station | `9091001001009509` | Commuter rail station | work |

Home address: Lugna gatan 15, 128 38 Skarpnäck (lat 59.270755, lon 18.114195).

---

## Lambda Logic

### Endpoint

```
GET /api/routes?from=home&to=work     (default)
GET /api/routes?from=work&to=home
```

### Query Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `from` | `home` | Origin location key (must exist in `LOCATIONS`) |
| `to` | `work` | Destination location key (must exist in `LOCATIONS`) |

Returns HTTP 400 if either key is not found in `LOCATIONS`.

### Flow

1. Parse `from` and `to` from query string, defaulting to `home` and `work`
2. Look up origin and destination in `LOCATIONS`
3. For each stop in the origin location, call the SL Trip Planner API against the first stop of the destination location:
   ```
   GET /v2/trips?type_origin=any&name_origin={origin_stop_id}&type_destination=any&name_destination={destination_stop_id}&calc_number_of_trips=3&calc_one_direction=true
   ```
4. From the response, extract:
   - First leg's departure time
   - Last leg's arrival time
   - Transport summary (line names for each non-walking leg)
5. Calculate `leave_by` = first leg departure time − origin stop's `walk_minutes`
6. Calculate `arrive_by` = last leg arrival time + destination stop's `walk_minutes`
7. Skip the route if `leave_by` is already in the past
8. Sort remaining routes by earliest `arrive_by` time
9. Select two routes: the fastest (earliest `arrive_by`), and from the rest, the one with the earliest `leave_by` time
10. Flag the fastest route as `fastest: true`
11. Return JSON

### Response Format

```json
{
  "generated_at": "2026-03-21T07:45:00+01:00",
  "from": "home",
  "to": "work",
  "origin": "Hemma",
  "destination": "Jobbet",
  "routes": [
    {
      "name": "Från Koloniområdet",
      "leave_by": "07:48",
      "departure": "07:51",
      "arrival": "08:37",
      "arrive_by": "08:39",
      "transfers": 2,
      "legs": ["🚌 816", "🚇 17", "🚆 41"],
      "transfer_stations": ["Skarpnäck", "T-Centralen"],
      "fastest": true
    },
    {
      "name": "Från Skarpnäck",
      "leave_by": "07:40",
      "departure": "07:52",
      "arrival": "08:42",
      "arrive_by": "08:44",
      "transfers": 1,
      "legs": ["🚇 17", "🚆 41"],
      "transfer_stations": ["T-Centralen"],
      "fastest": false
    }
  ]
}
```

### Error Handling

- If `from` or `to` is not a valid location key, return HTTP 400 with `{"error": "Unknown location: <key>"}`
- If the SL API returns no journeys for a route, that route is omitted from the response
- If all API calls fail, return `{"error": "Could not fetch trip data", "routes": []}`
- HTTP errors from the SL API are caught per-route (one failing route doesn't block others)

---

## Frontend

### Files

- `index.html` — single page, mobile-first layout
- `style.css` — styling

### Behavior

1. On page load, fetch `/api/routes?from=home&to=work` via `fetch()`
2. Display a direction toggle with two buttons: "→ Jobbet" and "→ Hemma"
3. Default selection: "→ Jobbet" (home→work)
4. Toggling direction fetches `/api/routes?from=work&to=home` (or vice versa)
5. Render route cards sorted by arrival time
6. Fastest route is visually highlighted (green border/background)
7. Each card shows:
   - Route name (from response)
   - "Leave by" time (label adapts: "Gå hemifrån" / "Gå från jobbet" based on `origin` in response)
   - Arrival time at final destination (`arrive_by`, including walk from stop)
   - Transit legs with transport mode icons (e.g. "🚌 816 → 🚇 17 → 🚆 41")
   - Transfer stations (e.g. "Byte vid Skarpnäck, T-Centralen")
8. Refresh button reloads current direction
9. Loading state while fetching
10. Error state if fetch fails

### Direction Toggle

The toggle is a pair of buttons at the top of the page. The active direction is visually highlighted. Tapping the other button switches direction and triggers a new fetch. The frontend reads `origin` and `destination` from the response to render context-aware labels (e.g. "Framme vid Jobbet" vs "Framme hemma").

### No Framework

Plain HTML + CSS + minimal vanilla JS (only for fetch + DOM rendering + direction toggle). No build step.

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
| Location-based config | Locations with stops defined as a Python dict. Supports bidirectional routing without duplicating stop data. |
| `from`/`to` query params | More flexible than a single `direction` enum. Maps directly to location keys and is extensible if more locations are added. |
| OAC for both origins | Origin Access Control for S3 and Lambda function URL. More security can be added later. |
| `calc_number_of_trips=3` | Fetch a few trips per route to find one that's still catchable after accounting for walk time. |
| `calc_one_direction=true` | Prevents the planner from returning trips that depart before now. |
| No CDK changes needed | CloudFront `/api/*` behavior already forwards query strings to Lambda via `ALL_VIEWER_EXCEPT_HOST_HEADER` origin request policy. |
