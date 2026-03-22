import json
import logging
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

logger = logging.getLogger()
logger.setLevel(logging.INFO)

LOCATIONS = {
    "home": {
        "name": "Hemma",
        "lat": 59.270755,
        "lon": 18.114195,
        "stops": [
            {"name": "Koloniområdet", "id": "9091001000001835", "walk_minutes": 3},
            {"name": "Skarpnäck", "id": "9091001000009140", "walk_minutes": 12},
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

ICON_WALK = "\U0001f6b6\u200d\u2642\ufe0f\u200d\u27a1\ufe0f"
ICON_METRO = "\U0001f687"
ICON_BUS = "\U0001f68c"
ICON_TRAIN = "\U0001f686"
ICON_TRAM = "\U0001f68a"

MODE_ICONS = {"Tunnelbana": ICON_METRO, "Buss": ICON_BUS, "Tåg": ICON_TRAIN, "Spårvagn": ICON_TRAM}

API_BASE = "https://journeyplanner.integration.sl.se/v2/trips"
TZ = ZoneInfo("Europe/Stockholm")


def fetch_trip(origin_id, destination_id):
    url = (
        f"{API_BASE}?type_origin=any&name_origin={origin_id}"
        f"&type_destination=any&name_destination={destination_id}"
        f"&calc_number_of_trips=3&calc_one_direction=true"
    )
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())


def parse_time(t):
    return datetime.fromisoformat(t).astimezone(TZ)


def fmt_time(dt):
    return dt.strftime("%H:%M")


def process_route(origin_stop, dest_stop):
    try:
        data = fetch_trip(origin_stop["id"], dest_stop["id"])
        now = datetime.now(TZ)

        for journey in data.get("journeys", []):
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
            leave_by = departure - timedelta(minutes=origin_stop["walk_minutes"])
            arrive_by = arrival + timedelta(minutes=dest_stop["walk_minutes"])

            if leave_by < now:
                continue

            transit_legs = []
            transfers = []
            for i, leg in enumerate(legs):
                if leg["transportation"].get("product", {}).get("name") in ("Gång", "footpath"):
                    transit_legs.append(ICON_WALK)
                else:
                    name = (
                        leg["transportation"].get("disassembledName")
                        or leg["transportation"].get("name", "?")
                    )
                    icon = MODE_ICONS.get(leg["transportation"].get("product", {}).get("name", ""), "")
                    transit_legs.append(f"{icon} {name}" if icon else name)
                if i > 0:
                    station = leg["origin"].get("parent", {}).get("disassembledName") or leg["origin"].get("name", "")
                    if station and not any(station in t or t in station for t in transfers):
                        transfers.append(station)

            return {
                "name": f"Från {origin_stop['name']}",
                "leave_by": fmt_time(leave_by),
                "departure": fmt_time(departure),
                "arrival": fmt_time(arrival),
                "arrive_by": fmt_time(arrive_by),
                "transfers": journey.get("interchanges", 0),
                "legs": transit_legs,
                "transfer_stations": transfers,
                "fastest": False,
                "_arrive_by_dt": arrive_by,
                "_leave_by_dt": leave_by,
            }

        logger.info("Route from '%s': no catchable trip found", origin_stop["name"])
        return None
    except Exception:
        logger.exception("Route from '%s' failed", origin_stop["name"])
        return None


def handler(event, context):
    params = event.get("queryStringParameters") or {}
    from_key = params.get("from", "home")
    to_key = params.get("to", "work")

    if from_key not in LOCATIONS:
        return {"statusCode": 400, "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": f"Unknown location: {from_key}"})}
    if to_key not in LOCATIONS:
        return {"statusCode": 400, "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": f"Unknown location: {to_key}"})}

    origin = LOCATIONS[from_key]
    destination = LOCATIONS[to_key]
    dest_stop = destination["stops"][0]

    results = [r for r in (process_route(s, dest_stop) for s in origin["stops"]) if r]
    results.sort(key=lambda r: r["_arrive_by_dt"])

    selected = []
    if results:
        fastest = results[0]
        fastest["fastest"] = True
        selected.append(fastest)
        rest = results[1:]
        if rest:
            rest.sort(key=lambda r: r["_leave_by_dt"])
            selected.append(rest[0])

    for r in selected:
        del r["_arrive_by_dt"]
        del r["_leave_by_dt"]

    body = {
        "generated_at": datetime.now(TZ).isoformat(),
        "from": from_key,
        "to": to_key,
        "origin": origin["name"],
        "destination": destination["name"],
        "routes": selected,
    }
    if not selected:
        body["error"] = "Could not fetch trip data"
        logger.warning("Zero routes returned")

    logger.info("Returning %d route(s) for %s→%s", len(selected), from_key, to_key)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }
