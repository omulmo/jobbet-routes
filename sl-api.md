# SL Journey Planner v2 API

## Overview

- Base URL: `https://journeyplanner.integration.sl.se/v2`
- Authentication: None required
- Format: JSON

## Endpoints

### Trip Search (used at runtime)

```
GET /v2/trips?type_origin=any&name_origin={origin_id}&type_destination=any&name_destination={destination_id}&calc_number_of_trips=1&calc_one_direction=true
```

| Parameter | Description |
|-----------|-------------|
| `type_origin` / `type_destination` | Always `any` |
| `name_origin` | Global stop ID (e.g. `9091001000001835`) |
| `name_destination` | Global stop ID for destination |
| `calc_number_of_trips` | Number of trips to return |
| `calc_one_direction` | `true` = only trips departing after now |

### Stop Finder (development only)

```
GET /v2/stop-finder?name_sf={query}&type_sf=any&any_obj_filter_sf=2
```

Used to look up stop IDs. Not called at runtime.

## Response Structure

```json
{
  "journeys": [
    {
      "tripDuration": 2880,
      "interchanges": 2,
      "legs": [...]
    }
  ]
}
```

### Leg Fields

| Field | Description |
|-------|-------------|
| `origin.departureTimePlanned` | Scheduled departure (ISO 8601) |
| `origin.departureTimeEstimated` | Real-time departure (may be absent) |
| `destination.arrivalTimePlanned` | Scheduled arrival |
| `destination.arrivalTimeEstimated` | Real-time arrival (may be absent) |
| `transportation.name` | Full name, e.g. `"Tunnelbana tunnelbanans gröna linje 17"` |
| `transportation.disassembledName` | Short line number, e.g. `"17"` |
| `transportation.product.name` | Transport type (see below) |

### Product Names

Observed values for `transportation.product.name`:

| API value | Meaning |
|-----------|---------|
| `Buss` | Bus |
| `Tunnelbana` | Metro |
| `Tåg` | Train (e.g. Pendeltåg) |
| `footpath` | Walking segment between stops |

**Important:** The solution design originally documented walking legs as `"Gång"`, but the actual API returns `"footpath"`. Our code handles both values.

Walking legs have `disassembledName: null` and `name: null`.

### Time Handling

- Prefer `departureTimeEstimated` / `arrivalTimeEstimated` when present (real-time data)
- Fall back to `departureTimePlanned` / `arrivalTimePlanned` (scheduled)
- Times are ISO 8601 with timezone offset

## Stop IDs Used

| Stop | Global ID | Type |
|------|-----------|------|
| Skarpnäcks koloniområde | `9091001000001835` | Bus stop |
| Skarpnäck (t-banan) | `9091001000009140` | Metro station |
| Skogskyrkogården | `9091001000009185` | Metro station |
| Solna station (destination) | `9091001001009509` | Commuter rail station |
