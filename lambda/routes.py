"""Route comparison business logic."""

import json
import logging
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import state
from models import find_location, find_trip, deduplicate_transfers

logger = logging.getLogger()

MODE_MAP = {"Tunnelbana": "metro", "Buss": "bus", "Tåg": "train", "Spårvagn": "tram"}

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
    """Fetch and process a single origin→destination stop pair. Returns best catchable route or None."""
    try:
        data = fetch_trip(origin_stop.stop_id, dest_stop.stop_id)
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
            leave_by = departure - timedelta(minutes=origin_stop.walk_minutes)
            arrive_by = arrival + timedelta(minutes=dest_stop.walk_minutes)

            if leave_by < now:
                continue

            transit_legs = []
            transfers = []
            for i, leg in enumerate(legs):
                product_name = leg["transportation"].get("product", {}).get("name", "")
                if product_name in ("Gång", "footpath"):
                    transit_legs.append({"line": "", "mode": "walk"})
                else:
                    name = (
                        leg["transportation"].get("disassembledName")
                        or leg["transportation"].get("name", "?")
                    )
                    mode = MODE_MAP.get(product_name, "bus")
                    transit_legs.append({"line": name, "mode": mode})
                if i > 0:
                    station = leg["origin"].get("parent", {}).get("disassembledName") or leg["origin"].get("name", "")
                    if station:
                        transfers.append(station)

            return {
                "name": f"Från {origin_stop.name}",
                "leave_by": fmt_time(leave_by),
                "departure": fmt_time(departure),
                "arrival": fmt_time(arrival),
                "arrive_by": fmt_time(arrive_by),
                "transfers": journey.get("interchanges", 0),
                "legs": transit_legs,
                "transfer_stations": deduplicate_transfers(transfers),
                "fastest": False,
                "_arrive_by_dt": arrive_by,
                "_leave_by_dt": leave_by,
            }

        return None
    except Exception:
        logger.exception("Route from '%s' failed", origin_stop.name)
        return None


def get_routes(trip_id: str | None = None, reverse: bool = False) -> dict:
    """Main route comparison. Returns API response dict."""
    s = state.load_state()

    # Resolve trip
    if trip_id:
        trip = find_trip(s, trip_id)
        if not trip:
            return {"error": f"Trip not found: {trip_id}", "routes": []}
    else:
        if not s.trips:
            return {"error": "No trips configured", "routes": []}
        trip = s.trips[0]

    origin_id = trip.origin_id
    dest_id = trip.destination_id
    if reverse:
        origin_id, dest_id = dest_id, origin_id

    origin = find_location(s, origin_id)
    dest = find_location(s, dest_id)
    if not origin or not dest:
        return {"error": "Trip references missing location", "routes": []}
    if not origin.stops or not dest.stops:
        return {"error": "Origin or destination has no stops", "routes": []}

    # Fetch routes for all origin stop × destination stop combinations
    results = []
    for o_stop in origin.stops:
        for d_stop in dest.stops:
            r = process_route(o_stop, d_stop)
            if r:
                results.append(r)

    results.sort(key=lambda r: r["_arrive_by_dt"])

    # Select: fastest + next departure
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
        "trip_id": trip.id,
        "reversed": reverse,
        "origin": origin.name,
        "destination": dest.name,
        "routes": selected,
    }
    if not selected:
        body["error"] = "Could not fetch trip data"

    return body
