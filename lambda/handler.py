import json
import urllib.request
from datetime import datetime, timedelta, timezone

DESTINATION_ID = "9091001001009509"  # Solna station

ROUTES = [
    {"name": "Buss från Koloniområdet", "walk_minutes": 3, "origin_id": "9091001000001835"},
    {"name": "T-bana från Skarpnäck", "walk_minutes": 12, "origin_id": "9091001000009140"},
    {"name": "T-bana från Skogskyrkogården", "walk_minutes": 15, "origin_id": "9091001000009185"},
]

API_BASE = "https://journeyplanner.integration.sl.se/v2/trips"
TZ = timezone(timedelta(hours=1))


def fetch_trip(origin_id):
    url = (
        f"{API_BASE}?type_origin=any&name_origin={origin_id}"
        f"&type_destination=any&name_destination={DESTINATION_ID}"
        f"&calc_number_of_trips=1&calc_one_direction=true"
    )
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())


def parse_time(t):
    return datetime.fromisoformat(t).astimezone(TZ)


def fmt_time(dt):
    return dt.strftime("%H:%M")


def process_route(route):
    try:
        data = fetch_trip(route["origin_id"])
        journey = data["journeys"][0]
        legs = journey["legs"]

        first_leg = legs[0]
        last_leg = legs[-1]

        departure = parse_time(
            first_leg["origin"].get("departureTimeEstimated")
            or first_leg["origin"]["departureTimePlanned"]
        )
        arrival = parse_time(
            last_leg["destination"].get("arrivalTimeEstimated")
            or last_leg["destination"]["arrivalTimePlanned"]
        )
        leave_by = departure - timedelta(minutes=route["walk_minutes"])

        now = datetime.now(TZ)
        if leave_by < now:
            return None

        transit_legs = []
        for leg in legs:
            if leg["transportation"].get("product", {}).get("name") in ("Gång", "footpath"):
                transit_legs.append("🚶‍♂️‍➡️")
            else:
                transit_legs.append(
                    leg["transportation"].get("disassembledName")
                    or leg["transportation"].get("name", "?")
                )

        return {
            "name": route["name"],
            "walk_minutes": route["walk_minutes"],
            "leave_home_by": fmt_time(leave_by),
            "departure": fmt_time(departure),
            "arrival": fmt_time(arrival),
            "transfers": journey.get("interchanges", 0),
            "legs": transit_legs,
            "fastest": False,
            "_arrival_dt": arrival,
        }
    except Exception:
        return None


def handler(event, context):
    results = [r for r in (process_route(route) for route in ROUTES) if r]
    results.sort(key=lambda r: r["_arrival_dt"])

    if results:
        results[0]["fastest"] = True

    for r in results:
        del r["_arrival_dt"]

    body = {
        "generated_at": datetime.now(TZ).isoformat(),
        "routes": results,
    }
    if not results:
        body["error"] = "Could not fetch trip data"

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }
